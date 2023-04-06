using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ThunderRoad;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace BaS_JP.Extensions
{
    public static class Vector3Extensions
    {
        /// <summary>
        /// Inverts each elements of Vector3
        /// </summary>
        public static Vector3 Invert(this Vector3 v)
        {
            return new Vector3(1 / v.x, 1 / v.y, 1 / v.z);
        }
        /// <summary>
        /// Inverts each elements of Vector3
        /// </summary>
        public static Vector2 Invert(this Vector2 v)
        {
            return new Vector2(1 / v.x, 1 / v.y);
        }
    }
    public static class DictionaryExtensions
    {
        /// <summary>
        ///  Python-like syntax sugar
        /// </summary>
        /// <typeparam name="TKey"></typeparam>
        /// <typeparam name="TValue"></typeparam>
        /// <param name="dictionary"></param>
        /// <param name="key"></param>
        /// <param name="defaultValue"></param>
        /// <returns></returns>
        public static TValue Get<TKey, TValue>(this IDictionary<TKey, TValue> dictionary, TKey key, TValue defaultValue)
        {
            if (key == null || !dictionary.TryGetValue(key, out TValue value))
                return defaultValue;
            return value;
        }
    }

    public static class LevelExtensions
    {
        public static bool ParseLevelOption(this Level level, string name, bool defaultValue)
        {
            if (level.options != null && level.options.TryGetValue(name, out string val))
            {
                if (val == "0")
                {
                    return false;
                }
                else
                {
                    return true;
                }
            }
            else
            {
                return true;
            }
        }
    }
}
