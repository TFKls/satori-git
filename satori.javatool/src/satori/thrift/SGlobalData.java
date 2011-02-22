package satori.thrift;

import satori.attribute.SAttributeReader;
import satori.common.SException;
import satori.session.SSession;
import satori.thrift.SAttributeData.AttributeWrap;
import satori.thrift.gen.Global;

public class SGlobalData {
	private static class GetJudgesCommand implements SThriftCommand {
		private AttributeWrap result;
		public SAttributeReader getResult() { return result; }
		@Override public void call() throws Exception {
			Global.Iface iface = new Global.Client(SThriftClient.getProtocol());
			long id = iface.Global_get_instance(SSession.getToken()).getId();
			result = new AttributeWrap(iface.Global_judges_get_map(SSession.getToken(), id));
		}
	}
	public static SAttributeReader getJudges() throws SException {
		GetJudgesCommand command = new GetJudgesCommand();
		SThriftClient.call(command);
		return command.getResult();
	}
}
