import SteckwerkCore
import SwiftUI
import UniformTypeIdentifiers

/// Themenpakete: installierte Pakete, Pakete aus dem Update-Kanal und lokale .swpaket-Dateien.
@MainActor
struct PackagesView: View {
    @EnvironmentObject var model: AppModel
    @State var kanal: UpdateCheck?
    @State var busy = false
    @State var message: String?
    @State var importing = false
    @State var removing: PaketInfo?

    var body: some View {
        Form {
            Section("Installiert") {
                let installed = model.schema?.pakete ?? []
                if installed.isEmpty {
                    Text("Noch keine Themenpakete installiert.")
                        .foregroundStyle(.secondary)
                }
                ForEach(installed) { paket in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(paket.name).fontWeight(.medium)
                            Text("\(paket.version) · \(paket.modelle.joined(separator: ", "))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            if let fehler = paket.fehler, !fehler.isEmpty {
                                Text(fehler).font(.caption).foregroundStyle(Theme.error)
                            }
                        }
                        Spacer()
                        Button(role: .destructive) {
                            removing = paket
                        } label: {
                            Image(systemName: "trash")
                        }
                        .buttonStyle(.borderless)
                        .help("Paket entfernen")
                        .disabled(busy)
                    }
                }
                Button {
                    importing = true
                } label: {
                    Label("Paketdatei (.swpaket) installieren …", systemImage: "doc.badge.plus")
                }
                .disabled(busy)
            }

            Section {
                if let kanal {
                    if kanal.pakete.isEmpty {
                        Text("Der Kanal bietet keine Pakete an.").foregroundStyle(.secondary)
                    }
                    ForEach(kanal.pakete) { paket in
                        HStack(alignment: .top) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(paket.name).fontWeight(.medium)
                                Text(paket.beschreibung)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(3)
                                Text(versionText(paket))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if paket.installable {
                                Button(paket.installiert == nil ? "Installieren" : "Aktualisieren") {
                                    run { try await $0.kanalPaketInstallieren(id: paket.id) }
                                }
                                .disabled(busy)
                            } else {
                                Label("aktuell", systemImage: "checkmark")
                                    .foregroundStyle(Theme.ok)
                                    .font(.caption)
                            }
                        }
                    }
                    if kanal.pakete.contains(where: \.installable) {
                        Button("Alle installieren und aktualisieren") {
                            run { try await $0.alleKanalPaketeInstallieren() }
                        }
                        .disabled(busy)
                    }
                } else {
                    Text("Pakete aus dem Steckwerk-Kanal laden – dafür braucht es eine Internetverbindung.")
                        .foregroundStyle(.secondary)
                }
                Button {
                    Task { await loadKanal() }
                } label: {
                    Label(kanal == nil ? "Kanal laden" : "Neu laden", systemImage: "arrow.clockwise")
                }
                .disabled(busy)
            } header: {
                Text("Aus dem Kanal")
            }

            if busy || message != nil {
                Section {
                    HStack {
                        if busy { ProgressView().controlSize(.small) }
                        if let message { Text(message).textSelection(.enabled) }
                    }
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Pakete")
        .fileImporter(isPresented: $importing,
                      allowedContentTypes: [UTType(filenameExtension: "swpaket") ?? .data],
                      allowsMultipleSelection: false) { result in
            guard case .success(let urls) = result, let url = urls.first else { return }
            installFile(url)
        }
        .confirmationDialog("Paket „\(removing?.name ?? "")“ entfernen?",
                            isPresented: Binding(get: { removing != nil }, set: { if !$0 { removing = nil } }),
                            titleVisibility: .visible) {
            Button("Entfernen", role: .destructive) {
                if let paket = removing {
                    run { try await $0.paketEntfernen(id: paket.id) }
                }
                removing = nil
            }
        }
    }

    private func versionText(_ paket: KanalPaket) -> String {
        var text = "Version \(paket.version)"
        if let installiert = paket.installiert, !installiert.isEmpty { text += " · installiert \(installiert)" }
        if !paket.benoetigt.isEmpty { text += " · braucht \(paket.benoetigt.joined(separator: ", "))" }
        return text
    }

    private func installFile(_ url: URL) {
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        do {
            let data = try Data(contentsOf: url)
            run { try await $0.paketInstallieren(data: data) }
        } catch {
            message = "Datei ließ sich nicht lesen: \(error.localizedDescription)"
        }
    }

    private func loadKanal() async {
        guard let client = model.client else { return }
        busy = true
        message = nil
        defer { busy = false }
        do {
            kanal = try await client.updateCheck()
        } catch {
            message = error.localizedDescription
        }
    }

    /// Führt eine Paketaktion aus und übernimmt das neue Schema der Engine.
    private func run(_ action: @escaping (EngineClient) async throws -> MessageResponse) {
        guard let client = model.client else { return }
        busy = true
        message = nil
        Task {
            defer { busy = false }
            do {
                let response = try await action(client)
                if let schema = response.schema {
                    model.apply(schema: schema)
                } else {
                    await model.reloadSchema()
                }
                message = response.message
                if kanal != nil {
                    kanal = try? await client.updateCheck()
                }
            } catch {
                message = error.localizedDescription
            }
        }
    }
}
