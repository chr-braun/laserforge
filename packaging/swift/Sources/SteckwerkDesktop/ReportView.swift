import SteckwerkCore
import SwiftUI

/// Prüfbericht nativ: Zusammenfassung grün/rot, Fehler, Montagehinweise und die einzelnen Prüfzeilen.
@MainActor
struct ReportView: View {
    let result: GenerateResponse

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Theme.spacing) {
                ForEach(result.assemblies) { assembly in
                    AssemblyReport(assembly: assembly)
                }
            }
            .padding(Theme.spacing)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

@MainActor
private struct AssemblyReport: View {
    let assembly: Assembly
    @State var showLines = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(assembly.summary, systemImage: assembly.ok ? "checkmark.seal.fill" : "xmark.octagon.fill")
                .font(.headline)
                .foregroundStyle(assembly.ok ? Theme.ok : Theme.error)
                .textSelection(.enabled)

            Text("\(assembly.parts) Teile · \(assembly.joints) Verbindungen · \(assembly.sheets.count) Blatt")
                .font(.caption)
                .foregroundStyle(.secondary)

            if !assembly.errors.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Fehler").font(.subheadline.bold())
                    ForEach(Array(assembly.errors.enumerated()), id: \.offset) { _, error in
                        Label(error, systemImage: "xmark.circle")
                            .foregroundStyle(Theme.error)
                            .textSelection(.enabled)
                    }
                }
            }

            if !assembly.notes.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Montagehinweise").font(.subheadline.bold())
                    ForEach(Array(assembly.notes.enumerated()), id: \.offset) { index, note in
                        HStack(alignment: .firstTextBaseline, spacing: 6) {
                            Text("\(index + 1).").monospacedDigit().foregroundStyle(.secondary)
                            Text(note).textSelection(.enabled)
                        }
                    }
                }
            }

            DisclosureGroup("Prüfbericht (\(ReportFormatter.lines(assembly.report).count) Zeilen)", isExpanded: $showLines) {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(ReportFormatter.lines(assembly.report).enumerated()), id: \.offset) { _, line in
                        Text(line.text)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(color(line.status))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(.top, 4)
            }
        }
        .card()
    }

    private func color(_ status: ReportStatus) -> Color {
        switch status {
        case .ok: return Theme.ok
        case .error: return Theme.error
        case .warning: return Theme.warning
        case .info: return .secondary
        }
    }
}
