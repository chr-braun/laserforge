import Foundation
import XCTest
@testable import SteckwerkCore

final class EngineLauncherTests: XCTestCase {
    func testArguments() {
        let args = EngineProcess.arguments(script: URL(fileURLWithPath: "/e/bridge_start.py"),
                                           engineRoot: URL(fileURLWithPath: "/e"), outDir: nil)
        XCTAssertEqual(args, ["-u", "/e/bridge_start.py", "--root", "/e"])
        let withOut = EngineProcess.arguments(script: URL(fileURLWithPath: "/e/b.py"), engineRoot: URL(fileURLWithPath: "/e"), outDir: "/o")
        XCTAssertEqual(Array(withOut.suffix(2)), ["--out", "/o"])
        XCTAssertFalse(args.contains("--no-browser"), "Das Startskript öffnet nie einen Browser")
    }

    func testParseStartLine() {
        XCTAssertEqual(EngineProcess.parseStartLine("STECKWERK_PORT=51234\n"), EngineStart(port: 51234, reused: false))
        XCTAssertEqual(EngineProcess.parseStartLine("Hallo\nSTECKWERK_PORT=8765 REUSED\n"), EngineStart(port: 8765, reused: true))
        XCTAssertNil(EngineProcess.parseStartLine("STECKWERK_PORT=\n"))
        XCTAssertNil(EngineProcess.parseStartLine("STECKWERK_PORT=99999"))
        XCTAssertNil(EngineProcess.parseStartLine("irgendwas"))
    }

    func testEngineRootPrefersEnvironmentThenBundle() {
        let exists: (String) -> Bool = { $0 == "/repo/webui.py" || $0 == "/App/Resources/engine/webui.py" }
        let res = URL(fileURLWithPath: "/App/Resources")
        XCTAssertEqual(EngineLocator.engineRoot(environment: ["STECKWERK_ROOT": "/repo"], resourceURL: res, fileExists: exists)?.path, "/repo")
        XCTAssertEqual(EngineLocator.engineRoot(environment: [:], resourceURL: res, fileExists: exists)?.path, "/App/Resources/engine")
        XCTAssertEqual(EngineLocator.engineRoot(environment: ["STECKWERK_ROOT": "/falsch"], resourceURL: res, fileExists: exists)?.path,
                       "/App/Resources/engine")
        XCTAssertNil(EngineLocator.engineRoot(environment: [:], resourceURL: nil, fileExists: exists))
    }

    func testBridgeScriptLocations() {
        let root = URL(fileURLWithPath: "/repo")
        XCTAssertEqual(EngineLocator.bridgeScript(engineRoot: root, fileExists: { $0 == "/repo/packaging/swift/bridge_start.py" })?.path,
                       "/repo/packaging/swift/bridge_start.py")
        XCTAssertEqual(EngineLocator.bridgeScript(engineRoot: root, fileExists: { $0.hasSuffix("bridge_start.py") })?.path,
                       "/repo/bridge_start.py")
        XCTAssertNil(EngineLocator.bridgeScript(engineRoot: root, fileExists: { _ in false }))
    }

    func testPythonCandidatesAndSelection() {
        let list = EngineLocator.pythonCandidates(environment: ["STECKWERK_PYTHON": "/mein/python3"], home: "/Users/x")
        XCTAssertEqual(list.first, "/mein/python3")
        XCTAssertEqual(list.last, "/usr/bin/python3")
        XCTAssertTrue(list.contains("/Users/x/.pyenv/shims/python3"))
        let found = EngineLocator.findPython(environment: [:], home: "/h", isUsable: { $0 == "/usr/local/bin/python3" })
        XCTAssertEqual(found, "/usr/local/bin/python3")
        XCTAssertNil(EngineLocator.findPython(environment: [:], home: "/h", isUsable: { _ in false }))
    }

    func testErrorTextsAreHelpful() {
        XCTAssertTrue(EngineLaunchError.pythonNotFound.localizedDescription.contains("Python"))
        XCTAssertEqual(EngineLaunchError.startFailed(details: "Traceback").details, "Traceback")
        XCTAssertEqual(EngineLaunchError.engineNotFound.details, "")
    }
}
