package satori.data;

import java.util.List;
import java.util.Map;

import satori.common.SPair;
import satori.task.SResultTask;
import satori.task.STaskException;
import satori.task.STaskManager;

public class SGlobal {
	public static Map<String, SBlob> getJudges() throws STaskException {
		return STaskManager.execute(new SResultTask<Map<String, SBlob>>() {
			@Override public Map<String, SBlob> run() throws Exception {
				return SGlobalData.getJudges();
			}
		});
	}
	
	public static List<SPair<String, String>> getDispatchers() throws STaskException {
		return STaskManager.execute(new SResultTask<List<SPair<String, String>>>() {
			@Override public List<SPair<String, String>> run() throws Exception {
				return SGlobalData.convertToList(SGlobalData.getDispatchers());
			}
		});
	}
	public static List<SPair<String, String>> getAccumulators() throws STaskException {
		return STaskManager.execute(new SResultTask<List<SPair<String, String>>>() {
			@Override public List<SPair<String, String>> run() throws Exception {
				return SGlobalData.convertToList(SGlobalData.getAccumulators());
			}
		});
	}
	public static List<SPair<String, String>> getReporters() throws STaskException {
		return STaskManager.execute(new SResultTask<List<SPair<String, String>>>() {
			@Override public List<SPair<String, String>> run() throws Exception {
				return SGlobalData.convertToList(SGlobalData.getReporters());
			}
		});
	}
}
