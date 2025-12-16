import Map from "./components/Map";
import { SourcesButton } from "@/app/lib/SourcesButton";
import { FeedbackButton } from "@/app/lib/FeedbackButton";

const HomePage: React.FC = () => {
  return (
    <>
      <Map />
      <SourcesButton href="https://suzlonenergy365-my.sharepoint.com/:w:/g/personal/45579_suzlon_com/IQDJIKnL2RipRbIV63siC7lZASGR1umFAFehwrGeP4ctWL4?e=B1iv8p" />
      <FeedbackButton href="https://suzlonenergy365-my.sharepoint.com/:x:/g/personal/45579_suzlon_com/IQDX0RtQMs35TIGgBehYPA8mAYji1vFTMPP0Os3N7mCtnjs?e=ov7SI4" />
    </>
  );
};

export default HomePage;
