// swift-tools-version:5.9
import PackageDescription

var products: [Product] = [
    .library(name: "SteckwerkCore", targets: ["SteckwerkCore"]),
]

var targets: [Target] = [
    .target(
        name: "SteckwerkCore",
        path: "Sources/SteckwerkCore"
    ),
    .testTarget(
        name: "SteckwerkCoreTests",
        dependencies: ["SteckwerkCore"],
        path: "Tests/SteckwerkCoreTests",
        resources: [.copy("Fixtures")]
    ),
]

// Die Oberfläche braucht SwiftUI/AppKit und entsteht nur auf macOS; der Kern baut und testet auch unter Linux.
#if os(macOS)
products.append(.executable(name: "SteckwerkDesktop", targets: ["SteckwerkDesktop"]))
targets.append(
    .executableTarget(
        name: "SteckwerkDesktop",
        dependencies: ["SteckwerkCore"],
        path: "Sources/SteckwerkDesktop"
    )
)
#endif

let package = Package(
    name: "SteckwerkDesktop",
    platforms: [.macOS(.v14)],
    products: products,
    targets: targets
)
