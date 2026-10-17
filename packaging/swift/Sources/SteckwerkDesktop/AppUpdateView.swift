import SteckwerkCore
import SwiftUI

/// Versionen und Update-Check (Programm und Pakete aus dem Steckwerk-Kanal).
@MainActor
struct AppUpdateView: View {
    @EnvironmentObject var model: AppModel
    @State var check: UpdateCheck?
    @State var busy = false
    @State var message: String?

    var body: some View {
        Form {
            Section("Version") {
                LabeledContent("Steckwerk Desktop", value: AppModel.appVersion)
                LabeledContent("Engine", value: model.engineVersion ?? "–")
            }

            Section {
                Button {
                    Task { await runCheck() }
                } label: {
                    Label("Nach Updates suchen", systemImage: "arrow.down.circle")
                }
                .disabled(busy)
                if busy { ProgressView().controlSize(.small) }

                if let check {
                    let p = check.programm
                    if p.neu {
                        VStack(alignment: .leading, spacing: 6) {
                            Label("Steckwerk \(p.version) ist verfügbar (installiert: \(p.installiert))",
                                  systemImage: "sparkles")
                                .foregroundStyle(Theme.accent)
                                .font(.headline)
                            ForEach(Array(p.hinweise.enumerated()), id: \.offset) { _, hinweis in
                                Text("• " + hinweis).font(.callout)
                            }
                            Text("Steckwerk Desktop aktualisiert sich nicht selbst: bitte die neue App laden und ersetzen.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    } else {
                        Label("Steckwerk \(p.installiert) ist aktuell", systemImage: "checkmark.circle")
                            .foregroundStyle(Theme.ok)
                    }

                    let paketUpdates = check.pakete.filter { $0.installiert != nil && $0.installable }
                    if paketUpdates.isEmpty {
                        Text("Alle installierten Pakete sind aktuell.")
                            .foregroundStyle(.secondary)
                    } else {
                        Text("Paket-Updates: " + paketUpdates.map { "\($0.name) \($0.version)" }.joined(separator: ", "))
                        Button("Alle Pakete aktualisieren") {
                            Task { await updatePakete() }
                        }
                        .disabled(busy)
                    }
                }
                if let message {
                    Text(message).textSelection(.enabled)
                }
            } header: {
                Text("Updates")
            } footer: {
                Text("Fragt den Steckwerk-Update-Kanal im Internet ab.")
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Updates")
    }

    private func runCheck() async {
        guard let client = model.client else { return }
        busy = true
        message = nil
        defer { busy = false }
        do {
            check = try await client.updateCheck()
        } catch {
            message = error.localizedDescription
        }
    }

    private func updatePakete() async {
        guard let client = model.client else { return }
        busy = true
        defer { busy = false }
        do {
            let response = try await client.alleKanalPaketeInstallieren()
            if let schema = response.schema { model.apply(schema: schema) }
            message = response.message
            check = try? await client.updateCheck()
        } catch {
            message = error.localizedDescription
        }
    }
}
