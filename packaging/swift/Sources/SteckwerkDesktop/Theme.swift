import AppKit
import SwiftUI

struct Theme {
    static let backgroundColor = NSColor(
        red: 245/255.0,
        green: 242/255.0,
        blue: 236/255.0,
        alpha: 1.0
    )

    static let cardColor = NSColor.white

    static let accentColor = NSColor(
        red: 180/255.0,
        green: 83/255.0,
        blue: 9/255.0,
        alpha: 1.0
    )

    static let darkBackgroundColor = NSColor(
        red: 30/255.0,
        green: 30/255.0,
        blue: 30/255.0,
        alpha: 1.0
    )

    static let darkCardColor = NSColor(
        red: 50/255.0,
        green: 50/255.0,
        blue: 50/255.0,
        alpha: 1.0
    )

    static let spacing: CGFloat = 12
    static let cornerRadius: CGFloat = 8
}
