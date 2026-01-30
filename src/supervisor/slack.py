"""
slack.py
A module that holds the constructs for using the Slack API with Block Kit
"""

import warnings
from abc import ABC, abstractmethod
from enum import Enum
from json import dumps
from typing import Any, Dict, List, Optional, Union

#: Slack Block Kit constants
MAX_BLOCKS = 50
MAX_CONTEXT_ELEMENTS = 10
MAX_SECTION_FIELD_ELEMENTS = 10
MAX_LENGTH_SECTION = 3000
MAX_LENGTH_SECTION_FIELD = 2000


def split_blocks(arr: List[Any], size: int) -> List[List[Any]]:
    """Split an array into chunks of specified size

    Parameters
    ----------
    arr : List[Any]
        Array to split
    size : int
        Size of each chunk

    Returns
    -------
    List[List[Any]]
        List of chunks
    """
    result = []
    while len(arr) > size:
        piece = arr[:size]
        result.append(piece)
        arr = arr[size:]

    result.append(arr)

    return result


class BlockType(Enum):
    """Available block type enums for Slack Block Kit"""

    SECTION = "section"
    DIVIDER = "divider"
    CONTEXT = "context"


class Block(ABC):
    """Base block containing attributes and behavior common to all blocks

    Block is an abstract class and cannot be sent directly.
    """

    def __init__(self, block: BlockType) -> None:
        self.type = block

    def _attributes(self) -> Dict[str, str]:
        return {"type": self.type.value}

    @abstractmethod
    def _resolve(self) -> Dict[str, Any]:
        """Resolve the block to a dictionary for Slack API"""

    def __repr__(self) -> str:
        return dumps(self._resolve(), indent=2)


class Text:
    """A text class formatted using Slack's markdown syntax"""

    def __init__(self, text: str) -> None:
        self.text = text

    def _resolve(self) -> Dict[str, str]:
        text = {
            "type": "mrkdwn",
            "text": self.text,
        }

        return text

    @staticmethod
    def to_text(text: str, max_length: Optional[int] = None) -> "Text":
        """Convert text to Text object with optional length limit

        Parameters
        ----------
        text : str
            Text to convert
        max_length : Optional[int]
            Maximum length for the text

        Returns
        -------
        Text
            Text object
        """
        # Replace empty strings with a single space to avoid Slack API errors
        if text == "":
            text = " "
        
        if max_length and len(text) > max_length:
            # Account for the truncation indicator in the max length
            truncation_indicator = "... (text truncated due to length)"
            adjusted_max_length = max_length - len(truncation_indicator)
            
            if adjusted_max_length > 0:
                text = text[:adjusted_max_length] + truncation_indicator
                warnings.warn(f"Text truncated from {len(text) + len(truncation_indicator)} to {max_length} characters")
            else:
                # If max_length is too small to accommodate the indicator, just truncate
                text = text[:max_length]
                warnings.warn(f"Text truncated to {max_length} characters")

        return Text(text=text)

    def __str__(self) -> str:
        return dumps(self._resolve(), indent=2)


class SectionBlock(Block):
    """A section is one of the most flexible blocks available"""

    def __init__(self, text: Optional[str] = None, fields: Optional[List[str]] = None) -> None:
        super().__init__(block=BlockType.SECTION)
        self.fields: List[Text] = []
        self.text: Optional[Text] = None

        if text is not None:
            self.text = Text.to_text(text, MAX_LENGTH_SECTION)
        if fields and len(fields) > 0:
            self.fields = [Text.to_text(field, MAX_LENGTH_SECTION_FIELD) for field in fields]

    def _resolve(self) -> Dict[str, Any]:
        section = self._attributes()

        if self.text:
            section["text"] = self.text._resolve()

        if self.fields and len(self.fields) > 0:
            section["fields"] = [field._resolve() for field in self.fields]

        return section


class ContextBlock(Block):
    """Displays message context. Typically used after a section"""

    def __init__(self, elements: List[str]) -> None:
        super().__init__(block=BlockType.CONTEXT)

        self.elements: List[Text] = []

        for element in elements:
            self.elements.append(Text.to_text(element, MAX_LENGTH_SECTION_FIELD))

        if len(self.elements) > MAX_CONTEXT_ELEMENTS:
            raise ValueError("Context blocks can hold a maximum of ten elements")

    def _resolve(self) -> Dict[str, Any]:
        context = self._attributes()
        context["elements"] = [element._resolve() for element in self.elements]

        return context


class DividerBlock(Block):
    """A content divider like an <hr>"""

    def __init__(self) -> None:
        super().__init__(block=BlockType.DIVIDER)

    def _resolve(self) -> Dict[str, Any]:
        return self._attributes()


class Message:
    """A Slack message object that can be converted to a JSON string for use with
    the Slack message API.
    """

    def __init__(self, text: str = "", blocks: Optional[Union[List[Block], Block]] = None) -> None:
        if isinstance(blocks, list):
            self.blocks: Optional[List[Block]] = blocks
        elif isinstance(blocks, Block):
            self.blocks = [blocks]
        else:
            self.blocks = None

        self.text = text

    def add(self, block: Block) -> None:
        """Add a block to the message

        Parameters
        ----------
        block : Block
            Block to add
        """
        if self.blocks is None:
            self.blocks = []

        self.blocks.append(block)

    def _resolve(self, blocks: Optional[List[Block]] = None) -> Dict[str, Any]:
        """Resolve the message to a dictionary for Slack API

        Parameters
        ----------
        blocks : Optional[List[Block]]
            Blocks to resolve, defaults to self.blocks

        Returns
        -------
        Dict[str, Any]
            Slack API message payload
        """
        if blocks is None:
            blocks = self.blocks

        message: Dict[str, Any] = {}
        if self.blocks:
            message["blocks"] = [block._resolve() for block in blocks]

        if self.text or self.text == "":
            message["text"] = self.text

        return message

    def json(self) -> str:
        """Convert message to JSON string

        Returns
        -------
        str
            JSON representation
        """
        return dumps(self._resolve(), indent=2)

    def get_messages(self) -> List[str]:
        """Get message split into multiple JSON strings if needed

        Returns
        -------
        List[str]
            List of JSON message strings
        """
        if self.blocks:
            splits = split_blocks(self.blocks, MAX_BLOCKS)
            splits = [dumps(self._resolve(blocks), indent=2) for blocks in splits]
            return splits
        return [self.json()]

    def __repr__(self) -> str:
        return self.json()

    def __getitem__(self, item: str) -> Any:
        return self._resolve()[item]

    def keys(self) -> Any:
        return self._resolve().keys()
