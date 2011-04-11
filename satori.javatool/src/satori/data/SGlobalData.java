package satori.data;

import static satori.data.SAttributeData.getBlobAttrMap;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import satori.common.SPair;
import satori.session.SSession;
import satori.task.STaskManager;
import satori.thrift.gen.Global;

class SGlobalData {
	static Map<String, SBlob> getJudges() throws Exception {
		STaskManager.log("Loading judges...");
		Global.Iface iface = new Global.Client(SSession.getProtocol());
		long id = iface.Global_get_instance(SSession.getToken()).getId();
		return Collections.unmodifiableMap(getBlobAttrMap(iface.Global_judges_get_map(SSession.getToken(), id)));
	}
	
	static Map<String, String> getDispatchers() throws Exception {
		STaskManager.log("Loading dispatchers...");
		Global.Iface iface = new Global.Client(SSession.getProtocol());
		return iface.Global_get_dispatchers(SSession.getToken());
	}
	static Map<String, String> getAccumulators() throws Exception {
		STaskManager.log("Loading accumulators...");
		Global.Iface iface = new Global.Client(SSession.getProtocol());
		return iface.Global_get_accumulators(SSession.getToken());
	}
	static Map<String, String> getReporters() throws Exception {
		STaskManager.log("Loading reporters...");
		Global.Iface iface = new Global.Client(SSession.getProtocol());
		return iface.Global_get_reporters(SSession.getToken());
	}
	
	static List<SPair<String, String>> convertToList(Map<String, String> map) {
		List<SPair<String, String>> result = new ArrayList<SPair<String, String>>();
		for (Map.Entry<String, String> entry : map.entrySet()) result.add(new SPair<String, String>(entry.getKey(), entry.getValue()));
		Collections.sort(result, new Comparator<SPair<String, String>>() {
			@Override public int compare(SPair<String, String> p1, SPair<String, String> p2) { return p1.first.compareTo(p2.first); }
		});
		return Collections.unmodifiableList(result);
	}
}
