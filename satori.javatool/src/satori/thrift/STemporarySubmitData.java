package satori.thrift;

import static satori.thrift.SAttributeData.convertAttrMap;
import static satori.thrift.SAttributeData.createBlobs;
import static satori.thrift.SAttributeData.createLocalAttrMap;
import static satori.thrift.SAttributeData.createRemoteAttrMap;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SAssert;
import satori.common.SException;
import satori.metadata.SOutputMetadata;
import satori.session.SSession;
import satori.test.STemporarySubmitReader;
import satori.test.STestReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.TemporarySubmit;
import satori.thrift.gen.TemporarySubmitStruct;

public class STemporarySubmitData {
	static class TemporarySubmitWrap implements STemporarySubmitReader {
		private final boolean pending;
		private final Map<SOutputMetadata, Object> result;
		public TemporarySubmitWrap(TemporarySubmitStruct struct, List<SOutputMetadata> meta, Map<String, AnonymousAttribute> data) throws SException {
			pending = struct.isPending();
			result = Collections.unmodifiableMap(createLocalAttrMap(meta, data));
		}
		@Override public boolean getPending() { return pending; }
		@Override public Map<SOutputMetadata, Object> getResult() { return result; }
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TemporarySubmitStruct struct;
		private Map<String, AnonymousAttribute> result;
		public TemporarySubmitStruct getStruct() { return struct; }
		public Map<String, AnonymousAttribute> getResult() { return result; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TemporarySubmit.Iface iface = new TemporarySubmit.Client(SThriftClient.getProtocol());
			struct = iface.TemporarySubmit_get_struct(SSession.getToken(), id);
			result = iface.TemporarySubmit_result_get_map(SSession.getToken(), id);
		}
	}
	public static STemporarySubmitReader load(long id, List<SOutputMetadata> meta) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return new TemporarySubmitWrap(command.getStruct(), meta, command.getResult());
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
		Map<String, Object> test_data = createRemoteAttrMap(test.getInput());
		test_data.put("judge", test.getJudge());
		createBlobs(submit_data);
		createBlobs(test_data);
		CreateCommand command = new CreateCommand(convertAttrMap(submit_data), convertAttrMap(test_data));
		SThriftClient.call(command);
		return command.getResult();
	}
}
