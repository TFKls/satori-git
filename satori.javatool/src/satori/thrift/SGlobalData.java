package satori.thrift;

import static satori.thrift.SAttributeData.getBlobAttrMap;

import java.util.Collections;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SException;
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
}
