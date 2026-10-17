import SwiftUI
import Foundation

@main
struct SteckwerkApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appDelegate.engineManager)
                .frame(minWidth: 1200, minHeight: 800)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .appMenu) {
                Text("Steckwerk Desktop")
                    .disabled(true)
                Divider()
                Button("Einstellungen") {
                    appDelegate.showPreferences()
                }
                .keyboardShortcut(",", modifiers: .command)
                Divider()
                Button("Steckwerk Desktop beenden") {
                    NSApplication.shared.terminate(nil)
                }
                .keyboardShortcut("q", modifiers: .command)
            }

            CommandGroup(replacing: .newDocument) {
                Button("Exportieren…") {
                    appDelegate.engineManager.exportAction()
                }
                .keyboardShortcut("e", modifiers: .command)
                .disabled(!appDelegate.engineManager.canExport)

                Button("Ordner öffnen") {
                    appDelegate.engineManager.openFolderAction()
                }
                .keyboardShortcut("o", modifiers: .command)
            }

            CommandGroup(replacing: .saveItem) {
                Button("Bauen & prüfen") {
                    appDelegate.engineManager.buildAction()
                }
                .keyboardShortcut("b", modifiers: .command)
            }
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    @Published var engineManager = EngineManager()
    private var preferencesWindow: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        engineManager.start()
    }

    func applicationWillTerminate(_ notification: Notification) {
        engineManager.stop()
    }

    func showPreferences() {
        if preferencesWindow == nil {
            let view = PreferencesView()
                .environmentObject(engineManager)
            let hostingController = NSHostingController(rootView: view)
            let window = NSWindow(contentViewController: hostingController)
            window.title = "Einstellungen"
            window.setFrameAutosaveName("PreferencesWindow")
            preferencesWindow = window
        }
        preferencesWindow?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

struct ContentView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var selectedTab: String = "models"

    var body: some View {
        ZStack {
            Color(nsColor: Theme.backgroundColor)
                .ignoresSafeArea()

            if engineManager.engineStatus == .stopped {
                VStack(spacing: 20) {
                    ProgressView()
                    Text("Engine wird gestartet…")
                        .font(.system(.body, design: .rounded))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if engineManager.engineError != nil {
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                        .font(.system(size: 48))
                    Text("Engine konnte nicht gestartet werden")
                        .font(.headline)
                    if let error = engineManager.engineError {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    Button("Erneut versuchen") {
                        engineManager.restart()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                NavigationSplitView {
                    ModelListView()
                        .environmentObject(engineManager)
                } detail: {
                    if let selectedModel = engineManager.selectedModel {
                        VStack(spacing: 0) {
                            ParameterForm(model: selectedModel)
                                .environmentObject(engineManager)
                            Divider()
                            HStack(spacing: 12) {
                                Button(action: { engineManager.buildAction() }) {
                                    Label("Bauen & prüfen", systemImage: "checkmark.circle")
                                }
                                .keyboardShortcut("b", modifiers: .command)

                                Spacer()

                                Text(engineManager.buildStatus)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding()
                        }
                    } else {
                        Text("Modell auswählen")
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(EngineManager())
}
