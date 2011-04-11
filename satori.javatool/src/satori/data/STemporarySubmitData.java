package satori.data;

import static satori.data.SAttributeData.convertAttrMap;
import static satori.data.SAttributeData.createBlobs;
import static satori.data.SAttributeData.createLocalAttrMap;
import static satori.data.SAttributeData.createRemoteAttrMap;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.common.SAssert;
import satori.metadata.SOutputMetadata;
import satori.session.SSession;
import satori.task.STaskManager;
import satori.test.STemporarySubmitReader;
import satori.test.STestReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.TemporarySubmit;
import satori.thrift.gen.TemporarySubmitStruct;

public class STemporarySubmitData {
	static class TemporarySubmitWrap implements STemporarySubmitReader {
		private final boolean pending;
		private final Map<SOutputMetadata, Object> result;
		public TemporarySubmitWrap(TemporarySubmitStruct struct, List<SOutputMetadata> meta, Map<String, AnonymousAttribute> data) {
			pending = struct.isPending();
			result = Collections.unmodifiableMap(createLocalAttrMap(meta, data));
		}
		@Override public boolean getPending() { return pending; }
		@Override public Map<SOutputMetadata, Object> getResult() { return result; }
	}
	
	public static STemporarySubmitReader load(long id, List<SOutputMetadata> meta) throws Exception {
		STaskManager.log("Loading temporary submit result...");
		TemporarySubmit.Iface iface = new TemporarySubmit.Client(SSession.getProtocol());
		return new TemporarySubmitWrap(iface.TemporarySubmit_get_struct(SSession.getToken(), id), meta, iface.TemporarySubmit_result_get_map(SSession.getToken(), id));
	}
	public static long create(SBlob submit, STestReader test) throws Exception {
		SAssert.assertNotNull(submit, "Submit is null");
		SAssert.assertNotNull(test.getJudge(), "Judge is null");
		Map<String, Object> submit_data = new HashMap<String, Object>();
		submit_data.put("content", submit);
		Map<String, Object> test_data = createRemoteAttrMap(test.getInput());
		test_data.put("judge", test.getJudge().getBlob());
		createBlobs(submit_data);
		createBlobs(test_data);
		STaskManager.log("Creating temporary submit...");
		TemporarySubmit.Iface iface = new TemporarySubmit.Client(SSession.getProtocol());
		return iface.TemporarySubmit_create(SSession.getToken(), convertAttrMap(test_data), convertAttrMap(submit_data)).getId();
	}
}
