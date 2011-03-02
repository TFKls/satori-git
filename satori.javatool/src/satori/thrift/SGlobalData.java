package satori.thrift;

import static satori.thrift.SAttributeData.getBlobAttrMap;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SException;
import satori.common.SPair;
import satori.session.SSession;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.Global;

public class SGlobalData {
	private static class GetJudgesCommand implements SThriftCommand {
		private Map<String, AnonymousAttribute> result;
		public Map<String, AnonymousAttribute> getResult() { return result; }
		@Override public void call() throws Exception {
			Global.Iface iface = new Global.Client(SThriftClient.getProtocol());
			long id = iface.Global_get_instance(SSession.getToken()).getId();
			result = iface.Global_judges_get_map(SSession.getToken(), id);
		}
	}
	public static Map<String, SBlob> getJudges() throws SException {
		GetJudgesCommand command = new GetJudgesCommand();
		SThriftClient.call(command);
		return Collections.unmodifiableMap(getBlobAttrMap(command.getResult()));
	}
	
	private static class GetDispatchersCommand implements SThriftCommand {
		private Map<String, String> result;
		public Map<String, String> getResult() { return result; }
		@Override public void call() throws Exception {
			Global.Iface iface = new Global.Client(SThriftClient.getProtocol());
			result = iface.Global_get_dispatchers(SSession.getToken());
		}
	}
	public static Map<String, String> getDispatchers() throws SException {
		GetDispatchersCommand command = new GetDispatchersCommand();
		SThriftClient.call(command);
		return Collections.unmodifiableMap(command.getResult());
	}
	
	private static class GetAccumulatorsCommand implements SThriftCommand {
		private Map<String, String> result;
		public Map<String, String> getResult() { return result; }
		@Override public void call() throws Exception {
			Global.Iface iface = new Global.Client(SThriftClient.getProtocol());
			result = iface.Global_get_accumulators(SSession.getToken());
		}
	}
	public static Map<String, String> getAccumulators() throws SException {
		GetAccumulatorsCommand command = new GetAccumulatorsCommand();
		SThriftClient.call(command);
		return Collections.unmodifiableMap(command.getResult());
	}
	
	private static class GetReportersCommand implements SThriftCommand {
		private Map<String, String> result;
		public Map<String, String> getResult() { return result; }
		@Override public void call() throws Exception {
			Global.Iface iface = new Global.Client(SThriftClient.getProtocol());
			result = iface.Global_get_reporters(SSession.getToken());
		}
	}
	public static Map<String, String> getReporters() throws SException {
		GetReportersCommand command = new GetReportersCommand();
		SThriftClient.call(command);
		return Collections.unmodifiableMap(command.getResult());
	}
	
	public static List<SPair<String, String>> convertToList(Map<String, String> map) {
		List<SPair<String, String>> result = new ArrayList<SPair<String, String>>();
		for (Map.Entry<String, String> entry : map.entrySet()) result.add(new SPair<String, String>(entry.getKey(), entry.getValue()));
		Collections.sort(result, new Comparator<SPair<String, String>>() {
			@Override public int compare(SPair<String, String> p1, SPair<String, String> p2) { return p1.first.compareTo(p2.first); }
		});
		return Collections.unmodifiableList(result);
	}
}
