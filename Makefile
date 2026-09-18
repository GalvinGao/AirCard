CLANG := xcrun clang
CFLAGS := -fobjc-arc -O2 -Wall -Wextra -arch arm64 -arch x86_64
FOUNDATION := -framework Foundation -framework CoreFoundation
MOBILEDEVICE := /System/Library/PrivateFrameworks/MobileDevice.framework/MobileDevice
AIRTRAFFIC := /System/Library/PrivateFrameworks/AirTrafficHost.framework/AirTrafficHost

.PHONY: all clean

all: build/device_helper build/airtraffic_host build/card_pdf

build:
	mkdir -p $@

build/device_helper: Sources/device_helper.m Sources/airlift_target.h | build
	$(CLANG) $(CFLAGS) $(FOUNDATION) $(MOBILEDEVICE) $< -o $@
	codesign --force --sign - $@

build/airtraffic_host: Sources/airtraffic_host.m | build
	$(CLANG) $(CFLAGS) $(FOUNDATION) $(AIRTRAFFIC) $< -o $@
	codesign --force --sign - $@

clean:
	rm -rf build

build/card_pdf: Sources/card_pdf.swift | build
	xcrun swiftc -O -target arm64-apple-macosx14.0 $< -o build/card_pdf_arm64
	xcrun swiftc -O -target x86_64-apple-macosx14.0 $< -o build/card_pdf_x86_64
	lipo -create build/card_pdf_arm64 build/card_pdf_x86_64 -output $@
	codesign --force --sign - $@
