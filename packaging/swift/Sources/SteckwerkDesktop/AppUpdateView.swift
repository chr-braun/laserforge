import SwiftUI

struct AppUpdateView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var isChecking = false
    @State private var updateAvailable = false
    @State private var newVersion: String?
    @State private var isUpdating = false

    var body: some View {
        VStack(spacing: 16) {
            Text("App-Update")
                .font(.title2)
                .fontWeight(.bold)

            VStack(spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Steckwerk Desktop")
                            .fontWeight(.medium)
                        Text("Version 2.8.0")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    if isChecking {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else if updateAvailable, let newVer = newVersion {
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("→ \(newVer) verfügbar")
                                .foregroundColor(.green)
                                .fontWeight(.medium)
                            Button(action: {
                                performUpdate()
                            }) {
                                if isUpdating {
                                    ProgressView()
                                } else {
                                    Text("Update")
                                }
                            }
                            .disabled(isUpdating)
                        }
                    } else {
                        Label("Aktuell", systemImage: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    }
                }
                .padding()
                .background(Color(nsColor: Theme.cardColor))
                .cornerRadius(8)
            }

            Button(action: {
                checkForUpdates()
            }) {
                Label("Nach Updates suchen", systemImage: "arrow.down.circle")
            }
            .disabled(isChecking || isUpdating)

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }

    private func checkForUpdates() {
        isChecking = true
        Task {
            do {
                if let response = try await engineManager.bridge?.updateCheck() {
                    await MainActor.run {
                        updateAvailable = response.verfuegbar
                        newVersion = response.version
                        isChecking = false
                    }
                }
            } catch {
                await MainActor.run {
                    isChecking = false
                }
            }
        }
    }

    private func performUpdate() {
        isUpdating = true
        Task {
            do {
                _ = try await engineManager.bridge?.updateProgramm()
                await MainActor.run {
                    isUpdating = false
                    updateAvailable = false
                }
            } catch {
                await MainActor.run {
                    isUpdating = false
                }
            }
        }
    }
}

#Preview {
    AppUpdateView()
        .environmentObject(EngineManager())
}
