import XCTest

class BridgeTests: XCTestCase {

    func testSchemaDecoding() throws {
        let json = """
        {
            "models": [
                {
                    "key": "test",
                    "label": "Test Model",
                    "desc": "A test",
                    "group": "Basis",
                    "params": []
                }
            ],
            "config": {
                "kerf": 0.3,
                "material_thickness": 3.0,
                "scale": 1.0
            },
            "motive": [],
            "pakete": []
        }
        """

        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let schema = try decoder.decode(Schema.self, from: data)

        XCTAssertEqual(schema.models.count, 1)
        XCTAssertEqual(schema.models[0].id, "test")
        XCTAssertEqual(schema.models[0].label, "Test Model")
    }

    func testParameterParsing() throws {
        let json = """
        {
            "key": "diameter",
            "label": "Durchmesser",
            "type": "num",
            "default": 100,
            "min": 10,
            "max": 500,
            "step": 1,
            "unit": "mm",
            "help": "Größe",
            "section": "Abmessungen",
            "options": null
        }
        """

        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let param = try decoder.decode(Schema.Parameter.self, from: data)

        XCTAssertEqual(param.key, "diameter")
        XCTAssertEqual(param.type, "num")
        XCTAssertEqual(param.min, 10)
        XCTAssertEqual(param.max, 500)
    }

    func testAnyCodableDecoding() throws {
        let values: [String] = [
            "\"text value\"",
            "42",
            "3.14",
            "true",
            "null"
        ]

        let decoder = JSONDecoder()

        for value in values {
            let data = value.data(using: .utf8)!
            _ = try decoder.decode(AnyCodable.self, from: data)
        }
    }
}
