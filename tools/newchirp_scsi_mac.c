/*
 * Minimal reusable macOS SCSI pass-through helper for NewChirp.
 *
 * This program only transfers caller-supplied CDBs and buffers. Radio
 * protocol and model policy belong in the Python profile layer.
 */

#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOCFPlugIn.h>
#include <IOKit/IOBSD.h>
#include <IOKit/IOKitLib.h>
#include <IOKit/scsi/SCSITaskLib.h>
#include <IOKit/storage/IOMedia.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void cf_string(CFTypeRef value, char *out, size_t size) {
    out[0] = '\0';
    if (value == NULL || CFGetTypeID(value) != CFStringGetTypeID()) {
        return;
    }
    CFStringGetCString((CFStringRef)value, out, size, kCFStringEncodingUTF8);
}

static CFTypeRef property(io_registry_entry_t service, const char *key) {
    CFStringRef name = CFStringCreateWithCString(
        kCFAllocatorDefault, key, kCFStringEncodingUTF8
    );
    CFTypeRef value = IORegistryEntryCreateCFProperty(
        service, name, kCFAllocatorDefault, 0
    );
    CFRelease(name);
    return value;
}

static void ancestor_strings(
    io_registry_entry_t service,
    char *vendor,
    size_t vendor_size,
    char *product,
    size_t product_size
) {
    io_registry_entry_t cursor = service;
    for (int depth = 0; depth < 16; depth++) {
        if (vendor[0] == '\0') {
            CFTypeRef value = property(cursor, "USB Vendor Name");
            cf_string(value, vendor, vendor_size);
            if (value) CFRelease(value);
        }
        if (product[0] == '\0') {
            CFTypeRef value = property(cursor, "USB Product Name");
            cf_string(value, product, product_size);
            if (value) CFRelease(value);
        }

        io_registry_entry_t parent = 0;
        kern_return_t result = IORegistryEntryGetParentEntry(
            cursor, kIOServicePlane, &parent
        );
        if (cursor != service) IOObjectRelease(cursor);
        if (result != KERN_SUCCESS || parent == 0) break;
        cursor = parent;
    }
    if (cursor != service) IOObjectRelease(cursor);
}

static int media_identity(
    io_registry_entry_t media,
    char *bsd,
    size_t bsd_size,
    char *vendor,
    size_t vendor_size,
    char *product,
    size_t product_size
) {
    CFTypeRef value = property(media, kIOBSDNameKey);
    cf_string(value, bsd, bsd_size);
    if (value) CFRelease(value);
    ancestor_strings(
        media, vendor, vendor_size, product, product_size
    );
    return bsd[0] != '\0';
}

static SCSITaskDeviceInterface **task_interface(io_registry_entry_t media) {
    io_registry_entry_t cursor = media;
    IOCFPlugInInterface **plugin = NULL;
    SCSITaskDeviceInterface **task = NULL;

    for (int depth = 0; depth < 16 && task == NULL; depth++) {
        SInt32 score = 0;
        kern_return_t result = IOCreatePlugInInterfaceForService(
            cursor,
            kIOSCSITaskDeviceUserClientTypeID,
            kIOCFPlugInInterfaceID,
            &plugin,
            &score
        );
        if (result == KERN_SUCCESS && plugin != NULL) {
            HRESULT query = (*plugin)->QueryInterface(
                plugin,
                CFUUIDGetUUIDBytes(kIOSCSITaskDeviceInterfaceID),
                (LPVOID *)&task
            );
            (*plugin)->Release(plugin);
            plugin = NULL;
            if (query != S_OK) task = NULL;
        }

        io_registry_entry_t parent = 0;
        result = IORegistryEntryGetParentEntry(
            cursor, kIOServicePlane, &parent
        );
        if (cursor != media) IOObjectRelease(cursor);
        if (result != KERN_SUCCESS || parent == 0) break;
        cursor = parent;
    }
    if (cursor != media) IOObjectRelease(cursor);
    return task;
}

static int list_devices(void) {
    io_iterator_t iterator = 0;
    io_service_t media = 0;
    kern_return_t result = IOServiceGetMatchingServices(
        kIOMainPortDefault,
        IOServiceMatching(kIOMediaClass),
        &iterator
    );
    if (result != KERN_SUCCESS) {
        fprintf(stderr, "Could not enumerate disk media: 0x%x\n", result);
        return 1;
    }

    int first = 1;
    printf("[");
    while ((media = IOIteratorNext(iterator)) != 0) {
        char bsd[64] = {0};
        char vendor[128] = {0};
        char product[128] = {0};
        CFTypeRef whole = property(media, kIOMediaWholeKey);
        int is_whole = (
            whole != NULL &&
            CFGetTypeID(whole) == CFBooleanGetTypeID() &&
            CFBooleanGetValue((CFBooleanRef)whole)
        );
        if (whole) CFRelease(whole);
        if (!media_identity(
                media, bsd, sizeof(bsd), vendor, sizeof(vendor),
                product, sizeof(product)
            ) || !is_whole) {
            IOObjectRelease(media);
            continue;
        }

        char trimmed_vendor[128];
        snprintf(trimmed_vendor, sizeof(trimmed_vendor), "%s", vendor);
        for (char *p = trimmed_vendor + strlen(trimmed_vendor);
             p > trimmed_vendor && p[-1] == ' '; p--) {
            p[-1] = '\0';
        }
        if (strcmp(trimmed_vendor, "STM") != 0 &&
            strstr(product, "microSD") == NULL) {
            IOObjectRelease(media);
            continue;
        }

        printf(
            "%s{\"port\":\"/dev/r%s\",\"deviceName\":\"%s %s\"}",
            first ? "" : ",",
            bsd,
            vendor,
            product
        );
        first = 0;
        IOObjectRelease(media);
    }
    printf("]\n");
    IOObjectRelease(iterator);
    return 0;
}

static io_service_t find_media(const char *device) {
    const char *bsd = strrchr(device, '/');
    bsd = bsd ? bsd + 1 : device;
    if (strncmp(bsd, "rdisk", 5) == 0) bsd++;

    io_iterator_t iterator = 0;
    if (IOServiceGetMatchingServices(
            kIOMainPortDefault,
            IOServiceMatching(kIOMediaClass),
            &iterator
        ) != KERN_SUCCESS) {
        return 0;
    }

    io_service_t media = 0;
    while ((media = IOIteratorNext(iterator)) != 0) {
        CFTypeRef value = property(media, kIOBSDNameKey);
        char current[64] = {0};
        cf_string(value, current, sizeof(current));
        if (value) CFRelease(value);
        if (strcmp(current, bsd) == 0) break;
        IOObjectRelease(media);
        media = 0;
    }
    IOObjectRelease(iterator);
    return media;
}

static int transfer_device(
    const char *device,
    const char *cdb_hex,
    size_t size,
    const char *write_hex,
    int write_transfer
) {
    if (strlen(cdb_hex) != 32) {
        fprintf(stderr, "CDB must contain exactly 16 bytes\n");
        return 2;
    }
    uint8_t cdb[16];
    for (int i = 0; i < 16; i++) {
        unsigned int value;
        if (sscanf(cdb_hex + i * 2, "%2x", &value) != 1) {
            fprintf(stderr, "Invalid CDB hex\n");
            return 2;
        }
        cdb[i] = (uint8_t)value;
    }

    io_service_t media = find_media(device);
    if (media == 0) {
        fprintf(stderr, "Disk media not found: %s\n", device);
        return 3;
    }
    SCSITaskDeviceInterface **interface = task_interface(media);
    IOObjectRelease(media);
    if (interface == NULL) {
        fprintf(stderr, "SCSI task interface is unavailable\n");
        return 4;
    }

    IOReturn result = (*interface)->ObtainExclusiveAccess(interface);
    if (result != kIOReturnSuccess) {
        fprintf(stderr, "Could not obtain exclusive disk access: 0x%x\n",
                result);
        (*interface)->Release(interface);
        return 5;
    }

    SCSITaskInterface **task = (*interface)->CreateSCSITask(interface);
    if (task == NULL) {
        (*interface)->ReleaseExclusiveAccess(interface);
        (*interface)->Release(interface);
        fprintf(stderr, "Could not create SCSI task\n");
        return 6;
    }

    void *buffer = calloc(1, size);
    if (buffer == NULL) {
        (*task)->Release(task);
        (*interface)->ReleaseExclusiveAccess(interface);
        (*interface)->Release(interface);
        return 7;
    }

    if (write_transfer) {
        if (strlen(write_hex) != size * 2) {
            fprintf(stderr, "Write payload length does not match --write\n");
            free(buffer);
            (*task)->Release(task);
            (*interface)->ReleaseExclusiveAccess(interface);
            (*interface)->Release(interface);
            return 2;
        }
        for (size_t i = 0; i < size; i++) {
            unsigned int value;
            if (sscanf(write_hex + i * 2, "%2x", &value) != 1) {
                fprintf(stderr, "Invalid write payload hex\n");
                free(buffer);
                (*task)->Release(task);
                (*interface)->ReleaseExclusiveAccess(interface);
                (*interface)->Release(interface);
                return 2;
            }
            ((uint8_t *)buffer)[i] = (uint8_t)value;
        }
    }

    IOVirtualRange range = {(IOVirtualAddress)buffer, size};
    (*task)->SetCommandDescriptorBlock(task, cdb, 16);
    (*task)->SetScatterGatherEntries(
        task,
        &range,
        1,
        size,
        write_transfer
            ? kSCSIDataTransfer_FromInitiatorToTarget
            : kSCSIDataTransfer_FromTargetToInitiator
    );
    (*task)->SetTimeoutDuration(task, 5000);

    SCSI_Sense_Data sense;
    memset(&sense, 0, sizeof(sense));
    SCSITaskStatus status = 0;
    UInt64 transferred = 0;
    result = (*task)->ExecuteTaskSync(
        task, &sense, &status, &transferred
    );

    int exit_code = 0;
    if (result != kIOReturnSuccess || status != 0 || transferred != size) {
        fprintf(
            stderr,
            "SCSI task failed: result=0x%x status=%u transferred=%llu/%zu\n",
            result,
            status,
            (unsigned long long)transferred,
            size
        );
        exit_code = 8;
    } else if (!write_transfer && fwrite(buffer, 1, size, stdout) != size) {
        fprintf(stderr, "Could not write SCSI response\n");
        exit_code = 9;
    }

    free(buffer);
    (*task)->Release(task);
    (*interface)->ReleaseExclusiveAccess(interface);
    (*interface)->Release(interface);
    return exit_code;
}

static int read_all(FILE *stream, void *buffer, size_t size) {
    size_t offset = 0;
    while (offset < size) {
        size_t count = fread((uint8_t *)buffer + offset, 1, size - offset,
                             stream);
        if (count == 0) return 0;
        offset += count;
    }
    return 1;
}

static int write_all(FILE *stream, const void *buffer, size_t size) {
    size_t offset = 0;
    while (offset < size) {
        size_t count = fwrite((const uint8_t *)buffer + offset, 1,
                              size - offset, stream);
        if (count == 0) return 0;
        offset += count;
    }
    return fflush(stream) == 0;
}

static int serve_device(const char *device) {
    io_service_t media = find_media(device);
    if (media == 0) {
        fprintf(stderr, "Disk media not found: %s\n", device);
        return 3;
    }
    SCSITaskDeviceInterface **interface = task_interface(media);
    IOObjectRelease(media);
    if (interface == NULL) {
        fprintf(stderr, "SCSI task interface is unavailable\n");
        return 4;
    }
    IOReturn result = (*interface)->ObtainExclusiveAccess(interface);
    if (result != kIOReturnSuccess) {
        fprintf(stderr, "Could not obtain exclusive disk access: 0x%x\n",
                result);
        (*interface)->Release(interface);
        return 5;
    }

    int exit_code = 0;
    for (;;) {
        uint8_t header[21];
        if (fread(header, 1, 1, stdin) == 0) break;
        if (!read_all(stdin, header + 1, sizeof(header) - 1)) {
            exit_code = 10;
            break;
        }

        int write_transfer = header[0] == 1;
        uint32_t size = ((uint32_t)header[1] << 24) |
                        ((uint32_t)header[2] << 16) |
                        ((uint32_t)header[3] << 8) |
                        header[4];
        uint8_t *cdb = header + 5;
        if (size == 0 || size > 65535) {
            const char *message = "Invalid transfer size";
            uint8_t response[5] = {1, 0, 0, 0, (uint8_t)strlen(message)};
            write_all(stdout, response, sizeof(response));
            write_all(stdout, message, strlen(message));
            continue;
        }

        uint8_t *buffer = calloc(1, size);
        if (buffer == NULL) {
            exit_code = 7;
            break;
        }
        if (write_transfer && !read_all(stdin, buffer, size)) {
            free(buffer);
            exit_code = 10;
            break;
        }

        SCSITaskInterface **task = (*interface)->CreateSCSITask(interface);
        if (task == NULL) {
            free(buffer);
            exit_code = 6;
            break;
        }
        IOVirtualRange range = {(IOVirtualAddress)buffer, size};
        (*task)->SetCommandDescriptorBlock(task, cdb, 16);
        (*task)->SetScatterGatherEntries(
            task,
            &range,
            1,
            size,
            write_transfer
                ? kSCSIDataTransfer_FromInitiatorToTarget
                : kSCSIDataTransfer_FromTargetToInitiator
        );
        (*task)->SetTimeoutDuration(task, 5000);

        SCSI_Sense_Data sense;
        memset(&sense, 0, sizeof(sense));
        SCSITaskStatus status = 0;
        UInt64 transferred = 0;
        result = (*task)->ExecuteTaskSync(
            task, &sense, &status, &transferred
        );
        (*task)->Release(task);

        char message[160];
        int failed = (
            result != kIOReturnSuccess ||
            status != 0 ||
            transferred != size
        );
        if (failed) {
            snprintf(
                message,
                sizeof(message),
                "SCSI task failed: result=0x%x status=%u "
                "transferred=%llu/%u",
                result,
                status,
                (unsigned long long)transferred,
                size
            );
        }
        uint32_t response_size = failed ? (uint32_t)strlen(message) :
                                (write_transfer ? 0 : size);
        uint8_t response[5] = {
            failed ? 1 : 0,
            (uint8_t)(response_size >> 24),
            (uint8_t)(response_size >> 16),
            (uint8_t)(response_size >> 8),
            (uint8_t)response_size,
        };
        if (!write_all(stdout, response, sizeof(response)) ||
            (response_size != 0 &&
             !write_all(stdout, failed ? (void *)message : buffer,
                        response_size))) {
            free(buffer);
            exit_code = 9;
            break;
        }
        free(buffer);
    }

    (*interface)->ReleaseExclusiveAccess(interface);
    (*interface)->Release(interface);
    return exit_code;
}

static void usage(void) {
    fprintf(
        stderr,
        "usage: newchirp_scsi --list | --device /dev/rdiskN "
        "--serve | --device /dev/rdiskN --cdb HEX32 "
        "(--read BYTES | --write HEX)\n"
    );
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--list") == 0) {
        return list_devices();
    }

    const char *device = NULL;
    const char *cdb = NULL;
    size_t size = 0;
    const char *write_hex = NULL;
    int serve = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--device") == 0 && i + 1 < argc) {
            device = argv[++i];
        } else if (strcmp(argv[i], "--cdb") == 0 && i + 1 < argc) {
            cdb = argv[++i];
        } else if (strcmp(argv[i], "--read") == 0 && i + 1 < argc) {
            size = (size_t)strtoul(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--write") == 0 && i + 1 < argc) {
            write_hex = argv[++i];
            size = strlen(write_hex) / 2;
        } else if (strcmp(argv[i], "--serve") == 0) {
            serve = 1;
        } else {
            usage();
            return 2;
        }
    }
    if (device == NULL ||
        (serve && (cdb != NULL || size != 0 || write_hex != NULL)) ||
        (!serve && (cdb == NULL || size == 0 || size > 65535 ||
                    (write_hex != NULL && strlen(write_hex) != size * 2)))) {
        usage();
        return 2;
    }
    if (serve) return serve_device(device);
    return transfer_device(device, cdb, size, write_hex, write_hex != NULL);
}
