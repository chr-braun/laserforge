import SwiftUI

struct MaterialView: View {
    @State private var temperatur = 20.0
    @State private var kerf = 0.2
    @State private var massstab = 1.0
    @State private var blattBreite = 600.0
    @State private var blattHoehe = 800.0

    var body: some View {
        VStack(spacing: 16) {
            Text("Materialparameter")
                .font(.title2)
                .fontWeight(.bold)

            Section(header: Text("Material").font(.headline)) {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Temperatur")
                        Slider(value: $temperatur, in: -40...60, step: 0.5)
                        Text(String(format: "%.1f°C", temperatur))
                            .frame(width: 70)
                    }

                    HStack {
                        Text("Schnittbreite (Kerf)")
                        Slider(value: $kerf, in: 0.01...1.0, step: 0.01)
                        Text(String(format: "%.2f mm", kerf))
                            .frame(width: 70)
                    }

                    HStack {
                        Text("Maßstab")
                        Slider(value: $massstab, in: 0.1...2.0, step: 0.1)
                        Text(String(format: "%.1f", massstab))
                            .frame(width: 50)
                    }
                }
            }

            Section(header: Text("Blatt").font(.headline)) {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Breite")
                        Slider(value: $blattBreite, in: 100...1000, step: 10)
                        Text(String(format: "%.0f mm", blattBreite))
                            .frame(width: 70)
                    }

                    HStack {
                        Text("Höhe")
                        Slider(value: $blattHoehe, in: 100...1000, step: 10)
                        Text(String(format: "%.0f mm", blattHoehe))
                            .frame(width: 70)
                    }
                }
            }

            Section(header: Text("Farben").font(.headline)) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Circle()
                            .fill(Color.black)
                            .frame(width: 24)
                        Text("Schnitt")
                    }

                    HStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 24)
                        Text("Gravur")
                    }
                }
            }

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

#Preview {
    MaterialView()
}
