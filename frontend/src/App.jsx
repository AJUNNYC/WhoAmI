import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  // Collect all possible browser signals
  const collectBrowserSignals = async () => {
    const signals = {};

    // ========== NAVIGATOR SIGNALS ==========
    signals.navigator = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      languages: navigator.languages,
      platform: navigator.platform,
      vendor: navigator.vendor,
      vendorSub: navigator.vendorSub,
      product: navigator.product,
      productSub: navigator.productSub,
      appName: navigator.appName,
      appVersion: navigator.appVersion,
      appCodeName: navigator.appCodeName,
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: navigator.deviceMemory,
      maxTouchPoints: navigator.maxTouchPoints,
      cookieEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack,
      onLine: navigator.onLine,
      pdfViewerEnabled: navigator.pdfViewerEnabled,
      webdriver: navigator.webdriver,
    };

    // ========== SCREEN SIGNALS ==========
    signals.screen = {
      width: screen.width,
      height: screen.height,
      availWidth: screen.availWidth,
      availHeight: screen.availHeight,
      colorDepth: screen.colorDepth,
      pixelDepth: screen.pixelDepth,
      orientation: screen.orientation?.type,
      orientationAngle: screen.orientation?.angle,
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      outerWidth: window.outerWidth,
      outerHeight: window.outerHeight,
      devicePixelRatio: window.devicePixelRatio,
      screenX: window.screenX,
      screenY: window.screenY,
      screenLeft: window.screenLeft,
      screenTop: window.screenTop,
    };

    // ========== TIMEZONE & LOCALE ==========
    signals.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    signals.tzOffsetMin = new Date().getTimezoneOffset();
    signals.locale = Intl.DateTimeFormat().resolvedOptions().locale;

    // ========== PERFORMANCE / TIMING ==========
    if (performance.timing) {
      signals.performance = {
        navigationStart: performance.timing.navigationStart,
        unloadEventStart: performance.timing.unloadEventStart,
        unloadEventEnd: performance.timing.unloadEventEnd,
        redirectStart: performance.timing.redirectStart,
        redirectEnd: performance.timing.redirectEnd,
        fetchStart: performance.timing.fetchStart,
        domainLookupStart: performance.timing.domainLookupStart,
        domainLookupEnd: performance.timing.domainLookupEnd,
        connectStart: performance.timing.connectStart,
        connectEnd: performance.timing.connectEnd,
        secureConnectionStart: performance.timing.secureConnectionStart,
        requestStart: performance.timing.requestStart,
        responseStart: performance.timing.responseStart,
        responseEnd: performance.timing.responseEnd,
        domLoading: performance.timing.domLoading,
        domInteractive: performance.timing.domInteractive,
        domContentLoadedEventStart: performance.timing.domContentLoadedEventStart,
        domContentLoadedEventEnd: performance.timing.domContentLoadedEventEnd,
        domComplete: performance.timing.domComplete,
        loadEventStart: performance.timing.loadEventStart,
        loadEventEnd: performance.timing.loadEventEnd,
        memory: performance.memory ? {
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          usedJSHeapSize: performance.memory.usedJSHeapSize,
        } : null,
      };
    }

    // ========== CANVAS FINGERPRINT ==========
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 200;
      canvas.height = 50;
      
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText('Browser Fingerprint', 2, 15);
      ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
      ctx.fillText('Canvas Test 🎨', 4, 17);
      
      signals.canvasFingerprintDataURL = canvas.toDataURL();
    } catch (e) {
      signals.canvasFingerprintDataURL = null;
    }

    // ========== WEBGL FINGERPRINT ==========
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        signals.webglRenderer = {
          vendor: gl.getParameter(gl.VENDOR),
          renderer: gl.getParameter(gl.RENDERER),
          version: gl.getParameter(gl.VERSION),
          shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
          unmaskedVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : null,
          unmaskedRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : null,
          maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
          maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
          maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
        };
      } else {
        signals.webglRenderer = null;
      }
    } catch (e) {
      signals.webglRenderer = null;
    }

    // ========== COMPUTED STYLES ==========
    signals.computedStyles = {
      colorScheme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      contrast: window.matchMedia('(prefers-contrast: high)').matches ? 'high' : 'normal',
      transparency: window.matchMedia('(prefers-reduced-transparency: reduce)').matches,
    };

    // ========== FONT DETECTION ==========
    signals.installedFontsDetection = detectFonts();

    // ========== AUDIO CONTEXT FINGERPRINT ==========
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        const audioCtx = new AudioContext();
        const oscillator = audioCtx.createOscillator();
        const analyser = audioCtx.createAnalyser();
        const gainNode = audioCtx.createGain();
        const scriptProcessor = audioCtx.createScriptProcessor(4096, 1, 1);

        gainNode.gain.value = 0;
        oscillator.connect(analyser);
        analyser.connect(scriptProcessor);
        scriptProcessor.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        signals.audioContextFingerprint = {
          sampleRate: audioCtx.sampleRate,
          state: audioCtx.state,
          maxChannelCount: audioCtx.destination.maxChannelCount,
          numberOfInputs: audioCtx.destination.numberOfInputs,
          numberOfOutputs: audioCtx.destination.numberOfOutputs,
          channelCount: audioCtx.destination.channelCount,
        };

        audioCtx.close();
      } else {
        signals.audioContextFingerprint = null;
      }
    } catch (e) {
      signals.audioContextFingerprint = null;
    }

    // ========== INTERACTION / BEHAVIORAL ==========
    signals.interaction = {
      mouseMovements: 0,
      keystrokes: 0,
      touchSupport: 'ontouchstart' in window,
      pointerEvents: 'onpointerdown' in window,
      clickCount: 0,
      scrollDepth: window.scrollY,
      timeOnPage: performance.now(),
    };

    // ========== CAPABILITIES ==========
    signals.capabilities = {
      webGL: !!window.WebGLRenderingContext,
      webGL2: !!window.WebGL2RenderingContext,
      webRTC: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      webWorker: !!window.Worker,
      serviceWorker: 'serviceWorker' in navigator,
      notifications: 'Notification' in window,
      geolocation: 'geolocation' in navigator,
      bluetooth: 'bluetooth' in navigator,
      usb: 'usb' in navigator,
      webAssembly: typeof WebAssembly === 'object',
      indexedDB: !!window.indexedDB,
      sessionStorage: !!window.sessionStorage,
      localStorage: !!window.localStorage,
      webSockets: 'WebSocket' in window,
      webAudio: !!(window.AudioContext || window.webkitAudioContext),
      canvas: !!document.createElement('canvas').getContext,
      svg: !!document.createElementNS && !!document.createElementNS('http://www.w3.org/2000/svg', 'svg').createSVGRect,
      speechRecognition: 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window,
      speechSynthesis: 'speechSynthesis' in window,
      vibrate: 'vibrate' in navigator,
      battery: 'getBattery' in navigator,
      deviceOrientation: 'DeviceOrientationEvent' in window,
      deviceMotion: 'DeviceMotionEvent' in window,
      touchEvents: 'ontouchstart' in window,
      pointerEvents: 'PointerEvent' in window,
      mediaDevices: !!(navigator.mediaDevices),
      clipboard: !!(navigator.clipboard),
      share: !!(navigator.share),
      credentials: !!(navigator.credentials),
      payment: 'PaymentRequest' in window,
      intersectionObserver: 'IntersectionObserver' in window,
      mutationObserver: 'MutationObserver' in window,
      resizeObserver: 'ResizeObserver' in window,
      performanceObserver: 'PerformanceObserver' in window,
    };

    // ========== STORAGE ==========
    try {
      if (navigator.storage && navigator.storage.estimate) {
        const estimate = await navigator.storage.estimate();
        signals.storage = {
          quota: estimate.quota,
          usage: estimate.usage,
          usagePercent: (estimate.usage / estimate.quota) * 100,
        };
      } else {
        signals.storage = null;
      }
    } catch (e) {
      signals.storage = null;
    }

    // ========== DEVICE MOTION ==========
    signals.deviceMotion = {
      supported: 'DeviceMotionEvent' in window,
      orientationSupported: 'DeviceOrientationEvent' in window,
    };

    // ========== DOCUMENT / NAVIGATION ==========
    signals.documentReferrer = document.referrer;
    signals.historyLength = history.length;
    signals.previousUrlPath = document.referrer ? new URL(document.referrer).pathname : null;

    // ========== MIME TYPES ==========
    if (navigator.mimeTypes) {
      signals.mimeTypes = Array.from(navigator.mimeTypes).map(mt => ({
        type: mt.type,
        description: mt.description,
        suffixes: mt.suffixes,
      }));
    } else {
      signals.mimeTypes = null;
    }

    // ========== PLUGINS ==========
    if (navigator.plugins) {
      signals.plugins = Array.from(navigator.plugins).map(plugin => ({
        name: plugin.name,
        description: plugin.description,
        filename: plugin.filename,
      }));
    } else {
      signals.plugins = null;
    }

    // ========== OS HINTS ==========
    signals.osHints = {
      userAgentData: navigator.userAgentData ? {
        brands: navigator.userAgentData.brands,
        mobile: navigator.userAgentData.mobile,
        platform: navigator.userAgentData.platform,
      } : null,
    };

    // ========== BATTERY STATUS ==========
    try {
      if (navigator.getBattery) {
        const battery = await navigator.getBattery();
        signals.batteryStatus = {
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime,
          level: battery.level,
        };
      } else {
        signals.batteryStatus = null;
      }
    } catch (e) {
      signals.batteryStatus = null;
    }

    return signals;
  };

  // Font detection helper
  const detectFonts = () => {
    const baseFonts = ['monospace', 'sans-serif', 'serif'];
    const testFonts = [
      'Arial', 'Verdana', 'Times New Roman', 'Courier New', 'Georgia',
      'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS', 'Trebuchet MS',
      'Impact', 'Lucida Console', 'Tahoma', 'Helvetica', 'Calibri',
      'Cambria', 'Consolas', 'Monaco', 'Courier', 'Lucida Sans'
    ];

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return [];
    
    const text = 'mmmmmmmmmmlli';
    const textSize = '72px';

    const baseMeasurements = {};
    baseFonts.forEach(baseFont => {
      ctx.font = `${textSize} ${baseFont}`;
      baseMeasurements[baseFont] = ctx.measureText(text).width;
    });

    const detectedFonts = [];
    testFonts.forEach(testFont => {
      let detected = false;
      baseFonts.forEach(baseFont => {
        ctx.font = `${textSize} '${testFont}', ${baseFont}`;
        const width = ctx.measureText(text).width;
        if (width !== baseMeasurements[baseFont]) {
          detected = true;
        }
      });
      if (detected) {
        detectedFonts.push(testFont);
      }
    });

    return detectedFonts;
  };

  // Send signals to backend
  const sendSignals = async (signals) => {
    try {
      const response = await fetch('http://localhost:8000/collect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signals),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Signals sent successfully:', result);
      return result;
    } catch (err) {
      console.error('❌ Failed to send signals:', err);
      throw err;
    }
  };

  // Auto-collect and send on mount
  useEffect(() => {
    const collectAndSend = async () => {
      try {
        console.log('🔍 Collecting browser signals...');
        const signals = await collectBrowserSignals();
        console.log('📊 Signals collected:', signals);
        
        console.log('📤 Sending to backend...');
        await sendSignals(signals);
      } catch (err) {
        console.error('Error in collection/send process:', err);
      }
    };

    collectAndSend();
  }, []);

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App