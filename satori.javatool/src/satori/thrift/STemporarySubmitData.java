package satori.thrift;

import static satori.thrift.SAttributeData.convertAttrMap;
import static satori.thrift.SAttributeData.createBlobs;
import static satori.thrift.SAttributeData.createRawAttrMap;

import java.util.HashMap;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SAssert;
import satori.common.SException;
import satori.session.SSession;
import satori.test.STemporarySubmitReader;
import satori.test.STestReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.TemporarySubmit;
import satori.thrift.gen.TemporarySubmitStruct;

public class STemporarySubmitData {
	static class TemporarySubmitWrap implements STemporarySubmitReader {
		private final boolean pending;
		private final String status;
		public TemporarySubmitWrap(TemporarySubmitStruct struct, Map<String, AnonymousAttribute> result) {
			pending = struct.isPending();
			AnonymousAttribute status_attr = result.get("status");
			status = status_attr != null ? status_attr.getValue() : null;
		}
		@Override public boolean getPending() { return pending; }
		@Override public String getStatus() { return status; }
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TemporarySubmitStruct temp_submit;
		private Map<String, AnonymousAttribute> result;
		public TemporarySubmitStruct getTempSubmit() { return temp_submit; }
		public Map<String, AnonymousAttribute> getResult() { return result; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TemporarySubmit.Iface iface = new TemporarySubmit.Client(SThriftClient.getProtocol());
			temp_submit = iface.TemporarySubmit_get_struct(SSession.getToken(), id);
			result = iface.TemporarySubmit_result_get_map(SSession.getToken(), id);
		}
	}
	public static STemporarySubmitReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return new TemporarySubmitWrap(command.getTempSubmit(), command.getResult());
	}
	
	private static class CreateCommand implements SThriftCommand {
		private final Map<String, AnonymousAttribute> submit_data;
		private final Map<String, AnonymousAttribute> test_data;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(Map<String, AnonymousAttribute> submit_data, Map<String, AnonymousAttribute> test_data) {
			this.submit_data = submit_data;
			this.test_data = test_data;
		}
		@Override public void call() throws Exception {
			TemporarySubmit.Iface iface = new TemporarySubmit.Client(SThriftClient.getProtocol());
			result = iface.TemporarySubmit_create(SSession.getToken(), test_data, submit_data).getId();
		}
	}
	public static long create(SBlob submit, STestReader test) throws SException {
		SAssert.assertNotNull(submit, "Submit is null");
		Map<String, Object> submit_data = new HashMap<String, Object>();
		submit_data.put("content", submit);
		Map<String, Object> test_data = createRawAttrMap(test.getInput());
		test_data.put("judge", test.getJudge());
		createBlobs(submit_data);
		createBlobs(test_data);
		CreateCommand command = new CreateCommand(convertAttrMap(submit_data), convertAttrMap(test_data));
		SThriftClient.call(command);
		return command.getResult();
	}
}
