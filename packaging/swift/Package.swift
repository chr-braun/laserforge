// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Steckwerk Desktop",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "SteckwerkDesktop",
            targets: ["SteckwerkDesktop"]
        )
    ],
    targets: [
        .executableTarget(
            name: "SteckwerkDesktop",
            dependencies: [],
            swiftSettings: [
                .unsafeFlags(["-suppress-warnings"], .when(configuration: .release))
            ]
        ),
        .testTarget(
            name: "SteckwerkDesktopTests",
            dependencies: ["SteckwerkDesktop"]
        )
    ]
)
