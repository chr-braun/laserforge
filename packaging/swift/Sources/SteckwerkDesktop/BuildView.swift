import SteckwerkCore
import SwiftUI

/// Rechte Seite: Bauen & prüfen, Ergebnisstatus, Vorschau, Prüfbericht und Export.
@MainActor
struct BuildView: View {
    @EnvironmentObject var model: AppModel
    let modelID: String

    private var result: GenerateResponse? {
        model.resultModelID == modelID ? model.result : nil
    }

    var body: some View {
        VStack(spacing: 0) {
            toolbar
                .padding(Theme.spacing)
            Divider()
            if let result {
                content(result)
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "hammer")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text("Mit „Bauen & prüfen“ (⌘B) entsteht der Blattplan.")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .background(Theme.background)
    }

    private var toolbar: some View {
        HStack(spacing: 10) {
            Button {
                Task { await model.build() }
            } label: {
                Label("Bauen & prüfen", systemImage: "checkmark.seal")
            }
            .buttonStyle(.borderedProminent)
            .disabled(model.isBuilding)

            if model.isBuilding {
                ProgressView().controlSize(.small)
            }

            if let result {
                StatusPill(result: result, stale: model.resultIsStale)
            }

            Spacer()

            if let message = model.statusMessage {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            Menu {
                Button("In Ordner exportieren … (⌘E)") {
                    Task { await model.exportToChosenFolder() }
                }
                Button("In den Steckwerk-Ordner speichern") {
                    Task { await model.saveToEngineFolder() }
                }
                .disabled(!model.canExport)
                Divider()
                Button("Steckwerk-Ordner öffnen") {
                    Task { await model.openFolder() }
                }
            } label: {
                Label("Exportieren", systemImage: "square.and.arrow.up")
            }
            .fixedSize()
        }
    }

    @ViewBuilder
    private func content(_ result: GenerateResponse) -> some View {
        if result.assemblies.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                Label("Nicht gebaut", systemImage: "xmark.octagon.fill")
                    .foregroundStyle(Theme.error)
                    .font(.headline)
                Text(result.error ?? "Die Engine hat nichts geliefert.")
                    .textSelection(.enabled)
            }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        } else {
            VSplitView {
                PreviewPane(result: result)
                    .frame(minHeight: 260, idealHeight: 420)
                ReportView(result: result)
                    .frame(minHeight: 160)
            }
        }
    }
}

@MainActor
private struct StatusPill: View {
    let result: GenerateResponse
    let stale: Bool

    var body: some View {
        let good = result.canExport
        HStack(spacing: 6) {
            Image(systemName: good ? "checkmark.circle.fill" : "xmark.octagon.fill")
            Text(ReportFormatter.statusText(result))
                .lineLimit(1)
            if stale {
                Text("· Werte geändert")
                    .foregroundStyle(.secondary)
            }
        }
        .font(.callout.weight(.medium))
        .foregroundStyle(good ? Theme.ok : Theme.error)
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(Capsule().fill((good ? Theme.ok : Theme.error).opacity(0.12)))
    }
}

/// Blattplan-Auswahl und native Vorschau.
@MainActor
private struct PreviewPane: View {
    @EnvironmentObject var model: AppModel
    let result: GenerateResponse

    private var sheets: [(title: String, sheet: SheetResult)] {
        result.assemblies.flatMap { a in a.sheets.map { (a.name + " · " + $0.file, $0) } }
    }

    var body: some View {
        let all = sheets
        let index = min(model.selectedSheet, max(all.count - 1, 0))
        VStack(spacing: 0) {
            if all.count > 1 {
                Picker("Blatt", selection: $model.selectedSheet) {
                    ForEach(all.indices, id: \.self) { i in
                        Text(all[i].title).tag(i)
                    }
                }
                .pickerStyle(.menu)
                .padding(.horizontal, Theme.spacing)
                .padding(.top, 8)
            }
            if model.geometry.indices.contains(index) {
                PreviewCanvas(geometry: model.geometry[index], checked: all[index].sheet.checked)
                    .padding(Theme.spacing)
            } else {
                Text("Keine Vorschau")
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
}
