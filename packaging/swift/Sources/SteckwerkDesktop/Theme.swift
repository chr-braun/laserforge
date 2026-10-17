import SwiftUI

struct Theme {
    static let warmBackground = Color(red: 0.96, green: 0.95, blue: 0.93)
    static let accentColor = Color(red: 0.71, green: 0.32, blue: 0.04)
    static let cardBackground = Color.white
    static let textPrimary = Color.black
    static let textSecondary = Color.gray
    static let successColor = Color(red: 0.2, green: 0.6, blue: 0.2)
    static let errorColor = Color(red: 0.7, green: 0.2, blue: 0.2)
    static let warningColor = Color(red: 0.9, green: 0.6, blue: 0.1)

    static let spacing8 = CGFloat(8)
    static let spacing12 = CGFloat(12)
    static let spacing16 = CGFloat(16)
    static let spacing20 = CGFloat(20)
    static let spacing24 = CGFloat(24)

    static let cornerRadius = CGFloat(8)
}

extension Color {
    static let warmBg = Theme.warmBackground
    static let accent = Theme.accentColor
}
