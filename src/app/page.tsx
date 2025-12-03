import Map from "./components/Map";
import { SourcesButton } from "@/app/lib/SourcesButton";

const HomePage: React.FC = () => {
  return (
    <>
      <Map />
      <SourcesButton href="https://data.humdata.org/dataset/ourairports-ind" />
    </>
  );
};

export default HomePage;
