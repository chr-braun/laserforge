import XCTest

class SchemaParsingTests: XCTestCase {

    func testSchemaDecoding() throws {
        let json = """
        {
            "models": [
                {
                    "id": "wichtelhaus",
                    "label": "Wichtelhaus",
                    "desc": "Ein Miniaturhaus",
                    "group": "Häuser",
                    "params": [
                        {
                            "type": "int",
                            "key": "tiefe",
                            "label": "Tiefe",
                            "default": 100,
                            "min": 50,
                            "max": 500,
                            "step": 10,
                            "unit": "mm",
                            "help": "Tiefe in Millimetern",
                            "section": "Abmessungen"
                        }
                    ]
                }
            ],
            "config": {
                "language": "de",
                "theme": "light"
            },
            "motive": [],
            "pakete": []
        }
        """

        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let schema = try decoder.decode(SchemaResponse.self, from: data)

        XCTAssertEqual(schema.models.count, 1)
        XCTAssertEqual(schema.models[0].id, "wichtelhaus")
        XCTAssertEqual(schema.models[0].params.count, 1)
        XCTAssertEqual(schema.models[0].params[0].key, "tiefe")
    }

    func testParamTypes() throws {
        let types = ["num", "int", "select", "flag", "text", "motiv", "motive"]

        for paramType in types {
            let json = """
            {
                "type": "\(paramType)",
                "key": "test_\(paramType)",
                "label": "Test \(paramType)",
                "default": 0,
                "options": null,
                "min": null,
                "max": null,
                "step": null,
                "unit": null,
                "help": null,
                "section": null
            }
            """

            let data = json.data(using: .utf8)!
            let decoder = JSONDecoder()
            let param = try decoder.decode(ParamSchema.self, from: data)
            XCTAssertEqual(param.type, paramType)
        }
    }
}
