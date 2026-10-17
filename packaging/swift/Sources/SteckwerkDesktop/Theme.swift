import AppKit
import SwiftUI

/// Warme Farben wie in der Weboberfläche; im Dunkelmodus Systemfarben.
enum Theme {
    static let background = Color(nsColor: NSColor(name: nil) { appearance in
        appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua
            ? .windowBackgroundColor
            : NSColor(srgbRed: 0xF5 / 255.0, green: 0xF2 / 255.0, blue: 0xEC / 255.0, alpha: 1)
    })

    static let card = Color(nsColor: NSColor(name: nil) { appearance in
        appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua ? .controlBackgroundColor : .white
    })

    static let accent = Color(nsColor: NSColor(srgbRed: 0xB4 / 255.0, green: 0x53 / 255.0, blue: 0x09 / 255.0, alpha: 1))

    static let cut = Color.primary
    static let engrave = Color(nsColor: NSColor(srgbRed: 0.15, green: 0.35, blue: 0.95, alpha: 1))
    static let ok = Color.green
    static let error = Color.red
    static let warning = Color.orange

    static let spacing: CGFloat = 12
    static let cornerRadius: CGFloat = 8
}

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Theme.spacing)
            .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
            .overlay(RoundedRectangle(cornerRadius: Theme.cornerRadius).stroke(Color.primary.opacity(0.08)))
    }
}

extension View {
    func card() -> some View { modifier(CardStyle()) }
}
