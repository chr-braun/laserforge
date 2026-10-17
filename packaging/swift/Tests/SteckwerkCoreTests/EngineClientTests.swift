import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import XCTest
@testable import SteckwerkCore

final class EngineClientTests: XCTestCase {
    private let base = URL(string: "http://127.0.0.1:8765")!

    func testPostRequestsCarryProtectionHeader() throws {
        let client = EngineClient(baseURL: base, transport: FakeTransport())
        let request = try client.makeRequest("api/generate", body: ["model": .string("wichtelhaus")])
        XCTAssertEqual(request.httpMethod, "POST")
        XCTAssertEqual(request.url?.absoluteString, "http://127.0.0.1:8765/api/generate")
        XCTAssertEqual(request.value(forHTTPHeaderField: "X-Steckwerk"), "1")
        XCTAssertEqual(request.value(forHTTPHeaderField: "Content-Type"), "application/json")
        let body = try JSONDecoder().decode([String: JSONValue].self, from: XCTUnwrap(request.httpBody))
        XCTAssertEqual(body["model"], .string("wichtelhaus"))
    }

    func testSchemaIsPlainGet() throws {
        let client = EngineClient(baseURL: base, transport: FakeTransport())
        let request = try client.makeRequest("api/schema", body: nil)
        XCTAssertEqual(request.httpMethod, "GET")
        XCTAssertNil(request.httpBody)
    }

    func testPortInitializerUsesLoopback() {
        XCTAssertEqual(EngineClient(port: 9123).baseURL.absoluteString, "http://127.0.0.1:9123")
    }

    func testErrorMessagesFromEngine() {
        let forbidden = Data(#"{"ok": false, "error": "Zugriff verweigert"}"#.utf8)
        XCTAssertThrowsError(try EngineClient.decode(PingResponse.self, data: forbidden, status: 403)) { error in
            XCTAssertEqual(error as? EngineError, .server("Zugriff verweigert"))
        }
        XCTAssertThrowsError(try EngineClient.decode(PingResponse.self, data: forbidden, status: 200)) { error in
            XCTAssertEqual(error as? EngineError, .server("Zugriff verweigert"))
        }
        XCTAssertThrowsError(try EngineClient.decode(PingResponse.self, data: Data("<html>".utf8), status: 500)) { error in
            XCTAssertEqual(error as? EngineError, .server("Die Engine meldet Fehler 500."))
        }
        XCTAssertThrowsError(try EngineClient.decode(UpdateCheck.self, data: Data("{}".utf8), status: 200)) { error in
            XCTAssertEqual(error as? EngineError, .invalidResponse)
        }
    }

    func testPingAndByeIdentifyTheApp() async throws {
        let fake = FakeTransport()
        fake.respond("/api/ping", json: #"{"ok": true, "app": "steckwerk", "version": "2.4.0", "pid": 1, "files": true}"#)
        fake.respond("/api/bye", json: #"{"ok": true}"#)
        let client = EngineClient(baseURL: base, transport: fake)
        let ping = try await client.ping()
        XCTAssertEqual(ping.version, "2.4.0")
        try await client.bye()
        XCTAssertEqual(try fake.body(of: 0)["client"], .string(EngineClient.clientID))
        XCTAssertEqual(try fake.body(of: 1)["client"], .string(EngineClient.clientID))
        XCTAssertEqual(fake.requests.map(\.httpMethod), ["POST", "POST"])
    }

    func testGenerateSendsModelParamsAndConfig() async throws {
        let fake = FakeTransport()
        fake.respond("/api/generate", data: try Fixture.data("generate_wichtelhaus"))
        let client = EngineClient(baseURL: base, transport: fake)
        let result = try await client.generate(model: "wichtelhaus", params: ["width": .double(80)], config: ["kerf": .double(0.2)])
        XCTAssertTrue(result.canExport)
        let body = try fake.body(of: 0)
        XCTAssertEqual(body["model"], .string("wichtelhaus"))
        XCTAssertEqual(body["params"]?.objectValue?["width"]?.doubleValue, 80)
        XCTAssertEqual(body["config"]?.objectValue?["kerf"]?.doubleValue, 0.2)
    }

    func testGenerateWithUnknownModelReturnsMessageInsteadOfThrowing() async throws {
        let fake = FakeTransport()
        fake.respond("/api/generate", data: try Fixture.data("generate_unknown_model"))
        let result = try await EngineClient(baseURL: base, transport: fake).generate(model: "gibtsnicht", params: [:], config: [:])
        XCTAssertFalse(result.ok)
        XCTAssertFalse(result.canExport)
        XCTAssertTrue(result.error?.contains("Unbekanntes Modell") == true)
        XCTAssertTrue(ReportFormatter.statusText(result).contains("Unbekanntes Modell"))
    }

    func testKeyGoesOnlyToBildEinstellungen() async throws {
        let fake = FakeTransport()
        fake.respond("/api/bild-einstellungen", json: #"{"ok": true, "bilder": {"key_gesetzt": true}}"#)
        let client = EngineClient(baseURL: base, transport: fake)
        try await client.bildEinstellungen(quelle: "chatgpt", key: "geheim-test")
        XCTAssertEqual(fake.requests.count, 1)
        XCTAssertEqual(fake.requests[0].url?.path, "/api/bild-einstellungen")
        XCTAssertEqual(try fake.body(of: 0), ["quelle": .string("chatgpt"), "key": .string("geheim-test")])
        XCTAssertFalse(fake.requests[0].url?.absoluteString.contains("geheim") ?? true, "Schlüssel nie in der URL")

        fake.respond("/api/bild-einstellungen", status: 400, json: #"{"ok": false, "error": "Der Schlüssel sieht nicht richtig aus"}"#)
        do {
            try await client.bildEinstellungen(quelle: "openrouter", key: "mit leerzeichen")
            XCTFail("Fehler erwartet")
        } catch {
            XCTAssertEqual(error as? EngineError, .server("Der Schlüssel sieht nicht richtig aus"))
        }
    }

    func testPaketInstallSendsBase64() async throws {
        let fake = FakeTransport()
        fake.respond("/api/paket-installieren", json: #"{"ok": true, "message": "Paket installiert", "schema": {"models": {}}}"#)
        let result = try await EngineClient(baseURL: base, transport: fake).paketInstallieren(data: Data([1, 2, 3]))
        XCTAssertEqual(result.message, "Paket installiert")
        XCTAssertNotNil(result.schema)
        XCTAssertEqual(try fake.body(of: 0)["data"], .string("AQID"))
    }

    func testUpdateCheckDecoding() throws {
        let check = try JSONDecoder().decode(UpdateCheck.self, from: Fixture.data("update_check"))
        XCTAssertFalse(check.programm.installiert.isEmpty)
        XCTAssertFalse(check.programm.version.isEmpty)
        XCTAssertFalse(check.pakete.isEmpty)
        XCTAssertTrue(check.pakete.allSatisfy { !$0.id.isEmpty })
    }

    func testKanalPaketInstallable() throws {
        let neu = try JSONDecoder().decode(KanalPaket.self, from: Data(#"{"id": "a", "version": "1.0", "installiert": null}"#.utf8))
        let gleich = try JSONDecoder().decode(KanalPaket.self, from: Data(#"{"id": "a", "version": "1.0", "installiert": "1.0"}"#.utf8))
        let alt = try JSONDecoder().decode(KanalPaket.self, from: Data(#"{"id": "a", "version": "1.1", "installiert": "1.0"}"#.utf8))
        XCTAssertTrue(neu.installable)
        XCTAssertFalse(gleich.installable)
        XCTAssertTrue(alt.installable)
    }

    func testAssistentAndBildResponses() throws {
        let vorschlag = try JSONDecoder().decode(AssistentVorschlag.self, from: Data(
            #"{"ok": true, "werte": {"width": 120}, "hinweis": "größer", "verworfen": ["foo"], "modell": "llama"}"#.utf8))
        XCTAssertEqual(vorschlag.werte["width"]?.doubleValue, 120)
        XCTAssertEqual(vorschlag.verworfen, ["foo"])
        let bild = try JSONDecoder().decode(BildErgebnis.self, from: Data(#"{"ok": true, "bild": "iVBORw0KGgo=", "typ": "image/svg+xml"}"#.utf8))
        XCTAssertEqual(bild.dateiendung, "svg")
        XCTAssertNotNil(bild.data)
    }
}
