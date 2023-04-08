using ThunderRoad;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace BaS_JP
{
    public class BASJP : ThunderScript
    {
        public override void ScriptLoaded(ModManager.ModData modData)
        {
            base.ScriptLoaded(modData);
        }
        public override void ScriptEnable()
        {
            ModManager.OnModLoad += ModManager_OnModLoad;
            base.ScriptEnable();
        }
        public override void ScriptDisable()
        {
            ModManager.OnModLoad -= ModManager_OnModLoad;
            base.ScriptDisable();
        }
        private void ModManager_OnModLoad(EventTime eventTime, ModManager.ModLoadEventType eventType, ModManager.ModData modData = null)
        {
            if(modData == null)
            {
                string currentLanguage = LocalizationManager.Instance.Language;
                EventManager.InvokeLanguageChanged("Bruh");
                EventManager.InvokeLanguageChanged(currentLanguage);
            }
        }
    }
}
