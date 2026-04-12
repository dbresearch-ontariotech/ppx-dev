import type { RequestHandler } from '@sveltejs/kit';

const BACKEND = 'http://localhost:8000';

export const fallback: RequestHandler = async ({ request, params }) => {
	const url = `${BACKEND}/api/ppx/${params.path}`;
	const response = await fetch(url, {
		method: request.method,
		headers: request.headers,
		body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
		// @ts-expect-error - duplex required for streaming body in Node
		duplex: 'half',
	});
	return new Response(response.body, {
		status: response.status,
		headers: response.headers,
	});
};
