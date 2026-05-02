import type {
  InlineNode,
  LessonBlock,
} from "../lib/lessons-api";

function renderInline(nodes: InlineNode[]) {
  return nodes.map((node, index) => {
    switch (node.kind) {
      case "link":
        return (
          <a
            key={index}
            href={node.href}
            target="_blank"
            rel="noreferrer"
            className="text-link"
          >
            {node.text}
          </a>
        );
      case "bold":
        return <strong key={index}>{node.text}</strong>;
      case "code":
        return (
          <code key={index} className="inline-code">
            {node.text}
          </code>
        );
      case "text":
      default:
        return <span key={index}>{node.text}</span>;
    }
  });
}

export function LessonContent({ blocks }: { blocks: LessonBlock[] }) {
  return (
    <>
      {blocks.map((block, blockIndex) => {
        if (block.kind === "paragraph") {
          return <p key={blockIndex}>{renderInline(block.inline)}</p>;
        }
        if (block.kind === "list") {
          return (
            <ul key={blockIndex} className="content-list">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInline(item)}</li>
              ))}
            </ul>
          );
        }
        if (block.kind === "subheading") {
          return <h4 key={blockIndex}>{block.text}</h4>;
        }
        return null;
      })}
    </>
  );
}
