#include <stdlib.h>

#include "my_application.h"

// Flutter's GTK window can stop presenting frames on some Wayland sessions
// while the app keeps running: on KDE Plasma with Intel + NVIDIA graphics a
// radio write finished but the window stayed on 18% until it was killed, and
// the same write ran normally with GDK_BACKEND=x11 (ledger w-20261121-ab4d).
// Prefer XWayland when it is available. GDK_BACKEND set by the user wins, and
// NEWCHIRP_WAYLAND=1 keeps the native Wayland backend.
static void prefer_xwayland() {
  if (getenv("GDK_BACKEND") != nullptr) return;
  const char* native = getenv("NEWCHIRP_WAYLAND");
  if (native != nullptr && native[0] == '1') return;
  const char* wayland = getenv("WAYLAND_DISPLAY");
  const char* x11 = getenv("DISPLAY");
  if (wayland == nullptr || wayland[0] == '\0') return;
  if (x11 == nullptr || x11[0] == '\0') return;
  setenv("GDK_BACKEND", "x11", 0);
}

int main(int argc, char** argv) {
  prefer_xwayland();
  g_autoptr(MyApplication) app = my_application_new();
  return g_application_run(G_APPLICATION(app), argc, argv);
}
