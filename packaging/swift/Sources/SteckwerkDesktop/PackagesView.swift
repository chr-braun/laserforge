import SwiftUI

struct PackagesView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var selectedFile: URL?
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 16) {
            Text("Paketmanager")
                .font(.title2)
                .fontWeight(.bold)

            Text("Installieren Sie zusätzliche Pakete über Kanäle oder lokale Dateien")
                .foregroundColor(.secondary)
                .font(.caption)

            VStack(spacing: 12) {
                if let pakete = engineManager.schema?.pakete {
                    ForEach(pakete, id: \.id) { paket in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(paket.label)
                                    .fontWeight(.medium)
                                if let kanal = paket.kanal {
                                    Text(kanal)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }

                            Spacer()

                            if let version = paket.version {
                                Text(version)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            Button(action: {
                                removePaket(paket.id)
                            }) {
                                Image(systemName: "trash")
                                    .foregroundColor(.red)
                            }
                            .buttonStyle(.borderless)
                        }
                        .padding()
                        .background(Color(nsColor: Theme.cardColor))
                        .cornerRadius(8)
                    }
                }
            }

            Divider()

            HStack(spacing: 12) {
                Button(action: {
                    selectLocalFile()
                }) {
                    Label("Lokale Datei…", systemImage: "folder")
                }
                .disabled(isLoading)

                Spacer()

                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }

    private func selectLocalFile() {
        let dialog = NSOpenPanel()
        dialog.title = "Paket-Datei auswählen"
        dialog.allowedContentTypes = []
        dialog.allowsMultipleSelection = false

        if dialog.runModal() == .OK, let url = dialog.url {
            isLoading = true
        }
    }

    private func removePaket(_ paketId: String) {
    }
}

#Preview {
    PackagesView()
        .environmentObject(EngineManager())
}
