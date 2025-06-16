import { useCohereClient } from '@/cohere-client';
import { FeedbackOption } from '@/types/feedbackOption';

const FEEDBACK_OPTIONS: readonly FeedbackOption[] = [
  { value: '🥹', rating: 1 },
  { value: '😕', rating: 2 },
  { value: '😐', rating: 3 },
  { value: '🙂', rating: 4 },
  { value: '🥰', rating: 5 },
];

export const useMessageFeedback = () => {
  const client = useCohereClient();

  const sendFeedback = async (
    messageId: string,
    startIndex: number,
    endIndex: number,
    rating: number
  ) => {
    try {
      await client.createMessageFeedback({
        message_id: messageId,
        start_index: startIndex,
        end_index: endIndex,
        rating,
      });
    } catch (error) {
      console.error('Failed to create message feedback:', error);
    }
  };

  return {
    feedbackOptions: FEEDBACK_OPTIONS,
    sendFeedback,
  };
};
