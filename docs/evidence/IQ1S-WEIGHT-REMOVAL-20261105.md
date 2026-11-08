# Retired IQ1_S weights removed — November 5, 2026

Deleted the retired Flash-Next IQ1_S checkpoint at the human's explicit request. **37,579,042,266 exclusive logical bytes (37.58GB /35.00GiB) were removed**, representing the10,946,618-byte metadata shard and37,568,095,648-byte model shard. Their allocated blocks totaled37,579,051,008bytes. The obsolete IQ1_S table filename was also unlinked and the now-empty old checkpoint directory removed.

**The active IQ1_M n-gram table remains intact:**28,800,138,432bytes, SHA256`05716382c280d999b81afff92b2d527fadbfd926ac225ffdc273f2d1d13331c6`. Its device/inode and size stayed unchanged; its hardlink count decreased from2 to1 when the obsolete IQ1_S alias was removed. The full table hash was verified before and after deletion. The28.8GB table's storage was not reclaimed or rewritten.

All deleted files matched their recorded publisher sizes/hashes and expected inodes/link counts; no open owner was found. Only the three exact retired filenames were removed. Private deletion receipts and metadata preimages retain original paths, hashes, source commit and reason; the weight payloads were intentionally not copied into an archive.

The qualified `flash-next-iq1m-strata` preset, native pack, three active IQ1_M shards,128K context, both GPUs, all guards, DSH selections and desktop routing are preserved. The IQ3_XXS entry is unchanged. Registry and retired runtime metadata now record deletion, replacing the earlier rollback-retention status. Restoring IQ1_S weights would require downloading them again; benchmark and qualification history remain available.

No model benchmark was repeated for this filesystem cleanup. Post-removal checks passed for retained checkpoint sizes, active table reference and selected preset/runtime/pack hashes without loading a model. Eight focused CPU regressions passed; API health and the IQ1_M model endpoint returned200. No cleanup job, GPU reservation or pending updater transaction remains; next action is normal IQ1_M use. [Existing qualified IQ1_M results and guards](FLASH-IQ1M-STRATA-20261105.md). [Sanitized deletion evidence](validation-results/20261105-iq1s-weight-removal.json).
