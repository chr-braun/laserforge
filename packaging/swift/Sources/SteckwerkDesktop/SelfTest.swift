import Foundation
import SteckwerkCore

/// `Steckwerk Desktop --self-test`: startet ohne Fenster die eingebaute Engine, baut das Wichtelhaus mit
/// Standardwerten und prüft „0 FEHLER“. Für CI und zur Fehlersuche; nutzt ein leeres temporäres HOME
/// und eigene Daten, berührt also weder Einstellungen noch Schlüsselbund.
enum SelfTest {
    static func runAndExit() -> Never {
        Task.detached {
            exit(await perform())
        }
        dispatchMain()
    }

    static func perform() async -> Int32 {
        let env = ProcessInfo.processInfo.environment
        guard let root = EngineLocator.engineRoot(environment: env, resourceURL: Bundle.main.resourceURL),
              let script = EngineLocator.bridgeScript(engineRoot: root) else {
            return failure(EngineLaunchError.engineNotFound.localizedDescription)
        }
        guard let python = EngineLocator.findPython(environment: env, home: NSHomeDirectory()) else {
            return failure(EngineLaunchError.pythonNotFound.localizedDescription)
        }
        let home = FileManager.default.temporaryDirectory.appendingPathComponent("steckwerk-selftest-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: home) }
        do {
            try FileManager.default.createDirectory(at: home, withIntermediateDirectories: true)
        } catch {
            return failure(error.localizedDescription)
        }
        var childEnv = env
        childEnv["HOME"] = home.path
        childEnv["STECKWERK_DATEN"] = home.appendingPathComponent("daten").path
        let engine = EngineProcess(python: python, script: script, engineRoot: root,
                                   outDir: home.appendingPathComponent("out").path, environment: childEnv)
        defer { engine.stop() }
        do {
            let start = try await engine.start()
            let client = EngineClient(port: start.port)
            let ping = try await client.ping()
            let schema = try await client.schema()
            guard let haus = schema.models["wichtelhaus"] else {
                return failure("Modell wichtelhaus fehlt")
            }
            let params = ParameterLogic.requestValues(haus.params, values: ParameterLogic.defaults(for: haus.params))
            let config = ParameterLogic.requestValues(schema.config, values: ParameterLogic.defaults(for: schema.config))
            let result = try await client.generate(model: "wichtelhaus", params: params, config: config)
            guard result.canExport, result.errorCount == 0 else {
                return failure("Wichtelhaus nicht CUT-READY: " + ReportFormatter.statusText(result))
            }
            let cut = result.assemblies.flatMap(\.sheets).map { SheetGeometry.parse(svg: $0.svg).cutCount }.reduce(0, +)
            guard cut > 0 else {
                return failure("Vorschau ohne Schnittlinien")
            }
            print("SELFTEST OK · Steckwerk Desktop \(AppModel.appVersion) · Engine \(ping.version ?? "?") · Python \(python)")
            print("SELFTEST OK · \(schema.models.count) Modelle · wichtelhaus: \(ReportFormatter.statusText(result)) · \(cut) Schnittlinien")
            try? await client.bye()
            return 0
        } catch let error as EngineLaunchError {
            return failure(error.localizedDescription + "\n" + error.details)
        } catch {
            return failure(error.localizedDescription + "\n" + engine.stderrTail)
        }
    }

    private static func failure(_ message: String) -> Int32 {
        FileHandle.standardError.write(Data(("SELFTEST FEHLER · " + message + "\n").utf8))
        return 1
    }
}
