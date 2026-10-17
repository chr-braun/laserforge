import SteckwerkCore
import SwiftUI

/// Material und Blatt: Stärke T, Kerf, Maßstab, Blattgröße, Farben – direkt aus schema.config.
@MainActor
struct MaterialView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        Form {
            Section {
                let params = model.schema?.config ?? []
                if params.isEmpty {
                    Text("Die Engine hat keine Material-Einstellungen geliefert.")
                        .foregroundStyle(.secondary)
                }
                ForEach(params) { param in
                    ParamRow(param: param, value: model.materialBinding(for: param))
                }
            } header: {
                Text("Material und Blatt")
            } footer: {
                Text("Gilt für alle Modelle und bleibt gespeichert. Nach einer Änderung neu bauen (⌘B).")
            }
            Section {
                HStack(spacing: 16) {
                    swatch(Theme.cut, "Schnitt")
                    swatch(Theme.engrave, "Gravur")
                }
                Button("Auf Standardwerte zurücksetzen") {
                    model.resetMaterial()
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Material")
    }

    private func swatch(_ color: Color, _ text: String) -> some View {
        HStack(spacing: 6) {
            RoundedRectangle(cornerRadius: 2).fill(color).frame(width: 18, height: 4)
            Text("\(text) in der Vorschau").font(.caption).foregroundStyle(.secondary)
        }
    }
}
