import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page-shell not-found-page">
      <section className="about-copy">
        <p className="eyebrow">Not found</p>
        <h1>That word is not in the current EtymoScape data.</h1>
        <p>
          The prototype only includes the JSON files currently present in
          data/final_data.
        </p>
        <Link className="primary-link" href="/">
          Back to search
        </Link>
      </section>
    </main>
  );
}
