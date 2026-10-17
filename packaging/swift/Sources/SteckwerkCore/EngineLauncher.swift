import Foundation
#if canImport(Glibc)
import Glibc
#elseif canImport(Darwin)
import Darwin
#endif

public struct EngineStart: Sendable, Equatable {
    public let port: Int
    public let reused: Bool

    public init(port: Int, reused: Bool) {
        self.port = port
        self.reused = reused
    }
}

public enum EngineLaunchError: LocalizedError, Equatable {
    case engineNotFound
    case pythonNotFound
    case startFailed(details: String)
    case timeout(details: String)

    public var errorDescription: String? {
        switch self {
        case .engineNotFound:
            return "Die Steckwerk-Engine wurde nicht gefunden. Die App enthält sie normalerweise selbst; "
                + "beim Entwickeln den Repo-Ordner über die Umgebungsvariable STECKWERK_ROOT angeben."
        case .pythonNotFound:
            return "Kein Python ab 3.9 gefunden. Bitte Python von python.org oder Apples Command Line Tools "
                + "(xcode-select --install) installieren; ein anderes Python über STECKWERK_PYTHON angeben."
        case .startFailed:
            return "Die Engine startet nicht."
        case .timeout:
            return "Die Engine hat sich nicht innerhalb von 15 Sekunden gemeldet."
        }
    }

    /// Letzte Ausgaben der Engine für den Bereich „Details“.
    public var details: String {
        switch self {
        case .startFailed(let d), .timeout(let d): return d
        default: return ""
        }
    }
}

/// Findet Engine-Ordner, Startskript und ein passendes Python.
public enum EngineLocator {
    public static let scriptName = "bridge_start.py"

    /// Reihenfolge: STECKWERK_ROOT, dann die in die App eingebaute Engine (Contents/Resources/engine).
    public static func engineRoot(environment: [String: String], resourceURL: URL?,
                                  fileExists: (String) -> Bool = { FileManager.default.fileExists(atPath: $0) }) -> URL? {
        var candidates: [URL] = []
        if let root = environment["STECKWERK_ROOT"], !root.isEmpty {
            candidates.append(URL(fileURLWithPath: root))
        }
        if let resourceURL {
            candidates.append(resourceURL.appendingPathComponent("engine"))
        }
        return candidates.first { fileExists($0.appendingPathComponent("webui.py").path) }
    }

    /// Das Startskript liegt in der App neben webui.py, im Repo unter packaging/swift.
    public static func bridgeScript(engineRoot: URL,
                                    fileExists: (String) -> Bool = { FileManager.default.fileExists(atPath: $0) }) -> URL? {
        let candidates = [
            engineRoot.appendingPathComponent(scriptName),
            engineRoot.appendingPathComponent("packaging/swift").appendingPathComponent(scriptName),
        ]
        return candidates.first { fileExists($0.path) }
    }

    /// Wie das Startskript der bestehenden Mac-App: Homebrew, python.org, pyenv, MacPorts, dann System-Python.
    public static func pythonCandidates(environment: [String: String], home: String) -> [String] {
        var list: [String] = []
        if let custom = environment["STECKWERK_PYTHON"], !custom.isEmpty {
            list.append(custom)
        }
        list += [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
            home + "/.pyenv/shims/python3",
            "/opt/local/bin/python3",
            "/usr/bin/python3",
        ]
        return list
    }

    public static func findPython(environment: [String: String], home: String,
                                  isUsable: (String) -> Bool = pythonIsUsable) -> String? {
        for path in pythonCandidates(environment: environment, home: home) {
            #if os(macOS)
            // /usr/bin/python3 ist nur ein Platzhalter, solange Apples Command Line Tools fehlen.
            if path == "/usr/bin/python3" && !commandLineToolsInstalled() { continue }
            #endif
            if isUsable(path) { return path }
        }
        return nil
    }

    public static func pythonIsUsable(_ path: String) -> Bool {
        guard FileManager.default.isExecutableFile(atPath: path) else { return false }
        return run(path, ["-c", "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"]) == 0
    }

    static func commandLineToolsInstalled() -> Bool {
        run("/usr/bin/xcode-select", ["-p"]) == 0
    }

    private static func run(_ path: String, _ arguments: [String], timeout: TimeInterval = 10) -> Int32? {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: path)
        process.arguments = arguments
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        do {
            try process.run()
        } catch {
            return nil
        }
        let deadline = Date().addingTimeInterval(timeout)
        while process.isRunning && Date() < deadline {
            usleep(20_000)
        }
        if process.isRunning {
            process.terminate()
            return nil
        }
        return process.terminationStatus
    }
}

/// Startet die Engine als Kindprozess und beendet sie wieder.
///
/// Die Engine hält stdin offen; schließt sich die Leitung (App beendet oder abgestürzt), beendet sie sich selbst.
public final class EngineProcess: @unchecked Sendable {
    private let process = Process()
    private let stdinPipe = Pipe()
    private let stdoutPipe = Pipe()
    private let stderrPipe = Pipe()
    private let lock = NSLock()
    private var stdoutText = ""
    private var stderrData = Data()
    private static let stderrLimit = 16 * 1024

    public init(python: String, script: URL, engineRoot: URL, outDir: String? = nil,
                environment: [String: String] = ProcessInfo.processInfo.environment) {
        process.executableURL = URL(fileURLWithPath: python)
        process.arguments = Self.arguments(script: script, engineRoot: engineRoot, outDir: outDir)
        process.currentDirectoryURL = engineRoot
        var env = environment
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        process.environment = env
        process.standardInput = stdinPipe
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe
    }

    public static func arguments(script: URL, engineRoot: URL, outDir: String?) -> [String] {
        var args = ["-u", script.path, "--root", engineRoot.path]
        if let outDir, !outDir.isEmpty {
            args += ["--out", outDir]
        }
        return args
    }

    /// Liest die Startzeile „STECKWERK_PORT=<port>“ (mit „REUSED“, wenn eine laufende Instanz mitbenutzt wird).
    public static func parseStartLine(_ text: String) -> EngineStart? {
        for line in text.split(whereSeparator: \.isNewline) {
            guard line.hasPrefix("STECKWERK_PORT=") else { continue }
            let rest = line.dropFirst("STECKWERK_PORT=".count).split(separator: " ")
            guard let first = rest.first, let port = Int(first), port > 0, port < 65536 else { continue }
            return EngineStart(port: port, reused: rest.dropFirst().contains("REUSED"))
        }
        return nil
    }

    public var isRunning: Bool { process.isRunning }

    public var processIdentifier: Int32 { process.processIdentifier }

    /// Die letzten Fehlerausgaben der Engine (für „Details“ im Fehlerdialog).
    public var stderrTail: String {
        lock.lock()
        defer { lock.unlock() }
        return String(decoding: stderrData, as: UTF8.self)
    }

    public func start(timeout: TimeInterval = 15) async throws -> EngineStart {
        stdoutPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard let self else { return }
            if data.isEmpty {
                handle.readabilityHandler = nil
                return
            }
            self.lock.lock()
            self.stdoutText += String(decoding: data, as: UTF8.self)
            self.lock.unlock()
        }
        stderrPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard let self else { return }
            if data.isEmpty {
                handle.readabilityHandler = nil
                return
            }
            self.lock.lock()
            self.stderrData.append(data)
            if self.stderrData.count > Self.stderrLimit {
                self.stderrData = self.stderrData.suffix(Self.stderrLimit)
            }
            self.lock.unlock()
        }

        do {
            try process.run()
        } catch {
            throw EngineLaunchError.startFailed(details: error.localizedDescription)
        }

        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if let started = currentStart() {
                return started
            }
            if !process.isRunning {
                try? await Task.sleep(nanoseconds: 200_000_000)
                if let started = currentStart() { return started }
                throw EngineLaunchError.startFailed(details: stderrTail)
            }
            try? await Task.sleep(nanoseconds: 50_000_000)
        }
        stop(grace: 0.5)
        throw EngineLaunchError.timeout(details: stderrTail)
    }

    private func currentStart() -> EngineStart? {
        lock.lock()
        defer { lock.unlock() }
        return Self.parseStartLine(stdoutText)
    }

    /// Leitung schließen, kurz warten, dann SIGTERM und nach 3 s SIGKILL.
    public func stop(grace: TimeInterval = 1.5) {
        try? stdinPipe.fileHandleForWriting.close()
        guard process.isRunning || process.processIdentifier != 0 else { return }
        if waitForExit(grace) { return }
        process.terminate()
        if waitForExit(3) { return }
        kill(process.processIdentifier, SIGKILL)
        _ = waitForExit(1)
    }

    private func waitForExit(_ seconds: TimeInterval) -> Bool {
        let deadline = Date().addingTimeInterval(seconds)
        while process.isRunning && Date() < deadline {
            usleep(20_000)
        }
        return !process.isRunning
    }
}
