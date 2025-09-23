import 'maplibre-gl/dist/maplibre-gl.css';
import '../globals.css';
import type { AppProps } from "next/app";

export default function MyApp({ Component, pageProps }: AppProps) {
    return <Component {...pageProps} />;
}
