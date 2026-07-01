import Map from "./components/Map";
import { SourcesButton } from "@/app/lib/SourcesButton";
import { FeedbackButton } from "@/app/lib/FeedbackButton";

const HomePage: React.FC = () => {
  return (
    <>
      <Map />
      <div
        style={{
          position: "fixed",
          bottom: 12,
          left: 12,
          zIndex: 1000,
          display: "flex",
          gap: 8,
        }}
      >
        <FeedbackButton />
        <SourcesButton href="https://suzlonenergy365-my.sharepoint.com/:w:/g/personal/45579_suzlon_com/IQDJIKnL2RipRbIV63siC7lZASGR1umFAFehwrGeP4ctWL4?e=B1iv8p" />
      </div>
    </>
  );
};

export default HomePage;
