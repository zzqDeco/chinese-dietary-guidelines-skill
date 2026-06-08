#!/usr/bin/env swift
import AppKit
import Foundation
import Vision

if CommandLine.arguments.count < 2 {
    fputs("usage: vision_ocr.swift IMAGE\n", stderr)
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let image = NSImage(contentsOf: imageURL),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("cannot load image: \(imageURL.path)\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest { request, error in
    if let error = error {
        fputs("Vision OCR error: \(error)\n", stderr)
        exit(1)
    }
    let observations = (request.results as? [VNRecognizedTextObservation]) ?? []
    let sorted = observations.sorted { a, b in
        let dy = abs(a.boundingBox.midY - b.boundingBox.midY)
        if dy > 0.012 {
            return a.boundingBox.midY > b.boundingBox.midY
        }
        return a.boundingBox.minX < b.boundingBox.minX
    }
    for obs in sorted {
        guard let top = obs.topCandidates(1).first else { continue }
        let box = obs.boundingBox
        print(String(format: "%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%@",
                     top.confidence, box.minX, box.minY, box.width, box.height, top.string))
    }
}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["zh-Hans", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])
