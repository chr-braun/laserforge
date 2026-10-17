import AppKit
import SteckwerkCore
import SwiftUI

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    let model = AppModel()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        model.shutdown()
    }
}

@main
@MainActor
enum Launcher {
    static func main() {
        if CommandLine.arguments.contains("--self-test") {
            SelfTest.runAndExit()
        }
        SteckwerkApp.main()
    }
}

struct SteckwerkApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate

    var body: some Scene {
        Window("Steckwerk Desktop", id: "main") {
            ContentView()
                .environmentObject(delegate.model)
                .frame(minWidth: 1000, minHeight: 680)
                .task { await delegate.model.startEngine() }
        }
        .defaultSize(width: 1280, height: 820)
        .commands { AppCommands(model: delegate.model) }

        Settings {
            SettingsView()
                .environmentObject(delegate.model)
        }
    }
}

@MainActor
struct AppCommands: Commands {
    @ObservedObject var model: AppModel

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("Exportieren …") {
                Task { await model.exportToChosenFolder() }
            }
            .keyboardShortcut("e", modifiers: .command)
            .disabled(model.selectedModelID == nil || model.engineState != .running)

            Button("Ordner öffnen") {
                Task { await model.openFolder() }
            }
            .keyboardShortcut("o", modifiers: .command)
            .disabled(model.engineState != .running)
        }

        CommandMenu("Modell") {
            Button("Bauen & prüfen") {
                Task { await model.build() }
            }
            .keyboardShortcut("b", modifiers: .command)
            .disabled(model.selectedModelID == nil || model.engineState != .running || model.isBuilding)

            Button("Auf Standardwerte zurücksetzen") {
                if let id = model.selectedModelID { model.resetValues(for: id) }
            }
            .disabled(model.selectedModelID == nil)

            Divider()

            Button("Engine neu starten") {
                model.restartEngine()
            }
        }

        CommandGroup(replacing: .help) {
            Button("Steckwerk Desktop – Hilfe") {
                model.alert = AppAlert(
                    title: "Steckwerk Desktop \(AppModel.appVersion)",
                    message: "Modell links wählen, Werte einstellen, mit ⌘B bauen und prüfen. Exportiert wird mit ⌘E – "
                        + "aber nur, wenn der Validator alles als CUT-READY bestätigt. Material und KI-Anbieter stellst du "
                        + "unter Einstellungen (⌘,) ein."
                )
            }
        }
    }
}
