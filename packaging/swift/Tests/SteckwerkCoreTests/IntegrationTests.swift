import Foundation
import XCTest
@testable import SteckwerkCore

/// Startet die echte Python-Engine. Läuft nur mit STECKWERK_ROOT (Repo-Ordner), z. B. in CI.
/// HOME zeigt auf einen leeren Ordner, damit keine echten Einstellungen oder Schlüssel berührt werden.
final class IntegrationTests: XCTestCase {
    private var home: URL!
    private var engine: EngineProcess?

    override func setUpWithError() throws {
        guard ProcessInfo.processInfo.environment["STECKWERK_ROOT"] != nil else {
            throw XCTSkip("STECKWERK_ROOT nicht gesetzt – Integrationstest übersprungen")
        }
        home = FileManager.default.temporaryDirectory.appendingPathComponent("steckwerk-home-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: home, withIntermediateDirectories: true)
    }

    override func tearDown() {
        engine?.stop()
        if let home { try? FileManager.default.removeItem(at: home) }
        super.tearDown()
    }

    private func launch() async throws -> (EngineProcess, EngineStart) {
        let env = ProcessInfo.processInfo.environment
        let root = try XCTUnwrap(EngineLocator.engineRoot(environment: env, resourceURL: nil))
        let script = try XCTUnwrap(EngineLocator.bridgeScript(engineRoot: root))
        let python = try XCTUnwrap(EngineLocator.findPython(environment: env, home: NSHomeDirectory()), "kein Python gefunden")
        var childEnv = env
        childEnv["HOME"] = home.path
        childEnv["XDG_STATE_HOME"] = home.appendingPathComponent("state").path
        childEnv["STECKWERK_DATEN"] = home.appendingPathComponent("daten").path
        let process = EngineProcess(python: python, script: script, engineRoot: root,
                                    outDir: home.appendingPathComponent("out").path, environment: childEnv)
        engine = process
        let start = try await process.start()
        return (process, start)
    }

    func testFullRoundTripWithWichtelhaus() async throws {
        let (process, start) = try await launch()
        XCTAssertFalse(start.reused, "Mit leerem HOME darf keine fremde Instanz mitbenutzt werden")
        let client = EngineClient(port: start.port)

        let ping = try await client.ping()
        XCTAssertEqual(ping.app, "steckwerk")

        let schema = try await client.schema()
        let haus = try XCTUnwrap(schema.models["wichtelhaus"])
        XCTAssertGreaterThan(schema.models.count, 10)
        XCTAssertTrue(schema.models.values.flatMap(\.params).allSatisfy { $0.kind != .unknown })

        let params = ParameterLogic.requestValues(haus.params, values: ParameterLogic.defaults(for: haus.params))
        let config = ParameterLogic.requestValues(schema.config, values: ParameterLogic.defaults(for: schema.config))
        let result = try await client.generate(model: "wichtelhaus", params: params, config: config)
        XCTAssertTrue(result.ok)
        XCTAssertEqual(result.errorCount, 0)
        XCTAssertTrue(ReportFormatter.statusText(result).hasPrefix("0 FEHLER"))
        XCTAssertTrue(result.canExport)

        let sheet = try XCTUnwrap(result.assemblies.first?.sheets.first)
        let geo = SheetGeometry.parse(svg: sheet.svg)
        XCTAssertGreaterThan(geo.cutCount, 0)
        XCTAssertEqual(geo.width, sheet.width)

        let target = home.appendingPathComponent("export")
        let written = try ReportFormatter.write(ReportFormatter.exportFiles(result), to: target)
        XCTAssertTrue(written.contains { $0.lastPathComponent == "pruefbericht.txt" })
        XCTAssertTrue(written.contains { $0.pathExtension == "svg" })

        let saved = try await client.save(model: "wichtelhaus", params: params, config: config)
        XCTAssertTrue(saved.files.contains { $0.hasSuffix("pruefbericht.txt") })

        do {
            try await client.bildEinstellungen(quelle: "chatgpt", key: "kein gültiger schlüssel")
            XCTFail("ein Schlüssel mit Leerzeichen muss abgelehnt werden")
        } catch let error as EngineError {
            XCTAssertTrue(error.localizedDescription.contains("Schlüssel"))
        }

        process.stop()
        XCTAssertFalse(process.isRunning)
    }

    func testEngineEndsWhenAppGoesAway() async throws {
        let (process, start) = try await launch()
        _ = try await EngineClient(port: start.port).ping()
        let begin = Date()
        process.stop(grace: 5)
        XCTAssertFalse(process.isRunning)
        XCTAssertLessThan(Date().timeIntervalSince(begin), 5, "Die Engine soll schon beim Schließen von stdin enden")
    }

    func testByeLetsEngineQuitOnItsOwn() async throws {
        let (process, start) = try await launch()
        let client = EngineClient(port: start.port)
        _ = try await client.ping()
        try await client.quit()
        let deadline = Date().addingTimeInterval(5)
        while process.isRunning && Date() < deadline {
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        XCTAssertFalse(process.isRunning)
    }
}
