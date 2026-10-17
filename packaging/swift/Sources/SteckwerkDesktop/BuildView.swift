import SwiftUI

struct BuildView: View {
    let response: GenerateResponse
    @State var showPreview = true

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing16) {
            HStack {
                if response.success {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .font(.title)

                    Text("Erfolgreich gebaut")
                        .font(.headline)
                } else {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundColor(.red)
                        .font(.title)

                    Text("Fehler beim Bauen")
                        .font(.headline)
                }

                Spacer()
            }

            if let validation = response.validationResult {
                ValidationReportView(validation: validation)
            }

            if let svg = response.svgContent {
                if showPreview {
                    PreviewCanvas(svgContent: svg)
                        .frame(height: 400)
                        .border(Color.gray.opacity(0.3))
                        .cornerRadius(Theme.cornerRadius)
                }

                HStack {
                    Button(action: { showPreview.toggle() }) {
                        Image(systemName: showPreview ? "eye.fill" : "eye.slash.fill")
                        Text(showPreview ? "Vorschau ausblenden" : "Vorschau zeigen")
                    }

                    Spacer()

                    Button(action: { exportSVG(svg) }) {
                        Image(systemName: "square.and.arrow.up.fill")
                        Text("Exportieren")
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(Theme.cornerRadius)
    }

    private func exportSVG(_ content: String) {
        let panel = NSSavePanel()
        panel.allowedFileTypes = ["svg"]
        panel.nameFieldStringValue = "design.svg"

        panel.begin { result in
            if result == .OK, let url = panel.url {
                try? content.write(to: url, atomically: true, encoding: .utf8)
            }
        }
    }
}

struct ValidationReportView: View {
    let validation: ValidationResult

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing12) {
            HStack {
                if validation.valid {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text("0 Fehler")
                        .font(.headline)
                } else {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text("\(validation.errors.count) Fehler")
                        .font(.headline)
                }
                Spacer()
            }

            if !validation.errors.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Fehler:")
                        .font(.caption)
                        .foregroundColor(.red)

                    ForEach(validation.errors, id: \.self) { error in
                        Text("• \(error)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }

            if !validation.warnings.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Warnungen:")
                        .font(.caption)
                        .foregroundColor(.orange)

                    ForEach(validation.warnings, id: \.self) { warning in
                        Text("• \(warning)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(validation.valid ? Color.green.opacity(0.1) : Color.red.opacity(0.1))
        .cornerRadius(Theme.cornerRadius)
    }
}

#Preview {
    BuildView(response: .init(
        success: true,
        polylines: nil,
        svgContent: "<svg></svg>",
        validationResult: .init(valid: true, errors: [], warnings: []),
        error: nil
    ))
    .padding()
    .background(Color.warmBg)
}
