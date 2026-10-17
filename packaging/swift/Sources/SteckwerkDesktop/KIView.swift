import SwiftUI

struct KIView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("KI-Anbieter")
                .font(.title2)
                .fontWeight(.bold)

            Text("Anbieter und API-Schlüssel stellst du unter Einstellungen (⌘,) ein. Schlüssel werden nur an die lokale Engine übergeben und dort im Schlüsselbund gespeichert.")
                .foregroundColor(.secondary)

            Text("Der KI-Assistent ist in dieser Version noch nicht an die App angebunden.")
                .font(.caption)
                .foregroundColor(.secondary)

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

#Preview {
    KIView()
}
