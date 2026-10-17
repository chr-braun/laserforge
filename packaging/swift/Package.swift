// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "SteckwerkDesktop",
    platforms: [
        .macOS(.v14)
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "SteckwerkDesktop",
            dependencies: [],
            path: "Sources/SteckwerkDesktop"
        ),
        .testTarget(
            name: "SteckwerkDesktopTests",
            dependencies: ["SteckwerkDesktop"],
            path: "Tests/SteckwerkDesktopTests"
        )
    ]
)
