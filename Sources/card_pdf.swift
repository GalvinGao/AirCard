import Foundation
import CoreGraphics
import ImageIO

// Wallet's 1536 × 969 artwork is a 512 × 323 point card at 3x.
guard CommandLine.arguments.count == 3 else {
    fputs("Usage: card_pdf input.png output.pdf\n", stderr)
    exit(1)
}
let input = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
var page = CGRect(x: 0, y: 0, width: 512, height: 323)
guard let source = CGImageSourceCreateWithURL(input as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil),
      let context = CGContext(output as CFURL, mediaBox: &page, nil) else {
    fputs("Could not decode artwork or create PDF\n", stderr)
    exit(1)
}
context.beginPDFPage(nil)
context.draw(image, in: page)
context.endPDFPage()
context.closePDF()
