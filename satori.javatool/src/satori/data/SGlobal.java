package satori.data;

import java.util.List;
import java.util.Map;

import satori.common.SPair;
import satori.task.SResultTask;
import satori.task.STaskException;
import satori.task.STaskHandler;

public class SGlobal {
	public static Map<String, SBlob> getJudges(final STaskHandler handler) throws STaskException {
		return handler.execute(new SResultTask<Map<String, SBlob>>() {
			@Override public Map<String, SBlob> run() throws Exception {
				return SGlobalData.getJudges(handler);
			}
		});
	}
	
	public static List<SPair<String, String>> getDispatchers(final STaskHandler handler) throws STaskException {
		return handler.execute(new SResultTask<List<SPair<String, String>>>() {
			@Override public List<SPair<String, String>> run() throws Exception {
				return SGlobalData.convertToList(SGlobalData.getDispatchers(handler));
			}
		});
	}
	public static List<SPair<String, String>> getAccumulators(final STaskHandler handler) throws STaskException {
		return handler.execute(new SResultTask<List<SPair<String, String>>>() {
			@Override public List<SPair<String, String>> run() throws Exception {
				return SGlobalData.convertToList(SGlobalData.getAccumulators(handler));
			}
		});
	}
	public static List<SPair<String, String>> getReporters(final STaskHandler handler) throws STaskException {
		return handler.execute(new SResultTask<List<SPair<String, String>>>() {
			@Override public List<SPair<String, String>> run() throws Exception {
				return SGlobalData.convertToList(SGlobalData.getReporters(handler));
			}
		});
	}
}
