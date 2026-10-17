import Foundation

public enum ReportStatus: Sendable, Hashable {
    case ok
    case warning
    case error
    case info
}

public struct ReportLine: Sendable, Hashable {
    public let status: ReportStatus
    public let text: String
}

public struct ExportFile: Sendable, Hashable {
    public let relativePath: String
    public let contents: String
}

/// Prüfbericht aufbereiten und Exportdateien zusammenstellen.
public enum ReportFormatter {
    public static func lines(_ report: String) -> [ReportLine] {
        report.split(separator: "\n", omittingEmptySubsequences: true).map { raw in
            let line = String(raw)
            let head = line.prefix(8).uppercased()
            let status: ReportStatus
            if head.hasPrefix("OK") {
                status = .ok
            } else if head.hasPrefix("FEHLER") || head.hasPrefix("ERROR") {
                status = .error
            } else if head.hasPrefix("WARN") || head.hasPrefix("HINWEIS") {
                status = .warning
            } else {
                status = .info
            }
            return ReportLine(status: status, text: line)
        }
    }

    /// Kurzfassung wie „0 FEHLER“ für die Statusanzeige.
    public static func statusText(_ response: GenerateResponse) -> String {
        if let error = response.error, response.assemblies.isEmpty {
            return error
        }
        let parts = response.assemblies.reduce(0) { $0 + $1.parts }
        let sheets = response.assemblies.reduce(0) { $0 + $1.sheets.count }
        let errors = response.errorCount
        let verdict = response.canExport ? "CUT-READY" : "nicht schneidbereit"
        return "\(errors) FEHLER · \(parts) Teile · \(sheets) Blatt · \(verdict)"
    }

    public static func pruefbericht(_ assembly: Assembly) -> String {
        var text = assembly.summary + "\n\n" + assembly.report
        if !assembly.notes.isEmpty {
            text += "\n\nMontagehinweise:\n" + assembly.notes.map { "- " + $0 }.joined(separator: "\n")
        }
        return text.hasSuffix("\n") ? text : text + "\n"
    }

    /// Dateien wie beim Speichern der Engine: je Baugruppe ein Ordner mit Blatt-SVGs und pruefbericht.txt.
    public static func exportFiles(_ response: GenerateResponse) -> [ExportFile] {
        guard response.canExport else { return [] }
        var files: [ExportFile] = []
        for assembly in response.assemblies {
            let folder = safeName(assembly.name, fallback: "modell")
            for sheet in assembly.sheets {
                files.append(ExportFile(relativePath: folder + "/" + safeName(sheet.file, fallback: "blatt.svg"),
                                        contents: sheet.svg))
            }
            files.append(ExportFile(relativePath: folder + "/pruefbericht.txt", contents: pruefbericht(assembly)))
        }
        return files
    }

    /// Schreibt die Dateien unter `folder`; gibt die geschriebenen Pfade zurück.
    @discardableResult
    public static func write(_ files: [ExportFile], to folder: URL) throws -> [URL] {
        var written: [URL] = []
        for file in files {
            let url = folder.appendingPathComponent(file.relativePath)
            try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
            try Data(file.contents.utf8).write(to: url, options: .atomic)
            written.append(url)
        }
        return written
    }

    /// Nur ein Dateiname ohne Ordneranteile, damit kein Pfad aus der Antwort außerhalb des Zielordners landet.
    static func safeName(_ name: String, fallback: String) -> String {
        let last = name.split(whereSeparator: { $0 == "/" || $0 == "\\" }).last.map(String.init) ?? ""
        let cleaned = last.filter { !$0.isNewline && $0 != "\0" && $0 != ":" }
        if cleaned.isEmpty || cleaned == "." || cleaned == ".." { return fallback }
        return cleaned
    }
}
