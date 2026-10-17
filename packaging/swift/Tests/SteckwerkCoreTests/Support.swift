import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import XCTest
@testable import SteckwerkCore

enum Fixture {
    static func data(_ name: String) throws -> Data {
        guard let url = Bundle.module.url(forResource: name, withExtension: "json", subdirectory: "Fixtures") else {
            throw XCTSkip("Fixture \(name).json fehlt")
        }
        return try Data(contentsOf: url)
    }

    static func schema() throws -> Schema {
        try JSONDecoder().decode(Schema.self, from: data("schema"))
    }

    static func generate() throws -> GenerateResponse {
        try JSONDecoder().decode(GenerateResponse.self, from: data("generate_wichtelhaus"))
    }
}

/// Transport ohne Netz: merkt sich Anfragen und liefert vorbereitete Antworten.
final class FakeTransport: HTTPTransport, @unchecked Sendable {
    private let lock = NSLock()
    private var responses: [String: (Data, Int)] = [:]
    private(set) var requests: [URLRequest] = []

    func respond(_ path: String, status: Int = 200, json: String) {
        lock.lock()
        responses[path] = (Data(json.utf8), status)
        lock.unlock()
    }

    func respond(_ path: String, status: Int = 200, data: Data) {
        lock.lock()
        responses[path] = (data, status)
        lock.unlock()
    }

    func send(_ request: URLRequest) async throws -> (Data, Int) {
        record(request)
    }

    private func record(_ request: URLRequest) -> (Data, Int) {
        lock.lock()
        defer { lock.unlock() }
        requests.append(request)
        let path = request.url?.path ?? ""
        guard let response = responses[path] else {
            return (Data(#"{"error": "nicht gefunden"}"#.utf8), 404)
        }
        return response
    }

    func body(of index: Int) throws -> [String: JSONValue] {
        let data = try XCTUnwrap(requests[index].httpBody)
        return try JSONDecoder().decode([String: JSONValue].self, from: data)
    }
}
